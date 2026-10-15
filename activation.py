"""Signed, device-bound Lisa activation. No provider keys or company secrets here.

The offline receipt is an ES256 entitlement verified against packaged public keys.
The private P-256 identity is protected by Windows user DPAPI and a local machine
digest. It proves possession during redemption/recovery; serials never leave the PC.
This discourages casual copying, rather than promising unbreakable client-side DRM.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from urllib import request, error
from urllib.parse import urlparse
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature

ISSUER = "lisa-kittycorp"
AUDIENCE = "lisa-desktop"
KEY_ID = "lisa-license-2026-22"
PURCHASE_URL = "https://kittycorp.vercel.app/"

def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

def _unb64(value: str) -> bytes:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("Invalid signed data.")
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

def _protect(value: bytes, decrypt=False) -> bytes:
    from core import dpapi
    return dpapi(value, decrypt)

def _machine_binding() -> str:
    if os.name != "nt":
        raise RuntimeError("Lisa device activation requires Windows.")
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0,
                        winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
        guid = str(winreg.QueryValueEx(key, "MachineGuid")[0]).strip().lower()
    if not guid:
        raise RuntimeError("Windows device identity could not be read.")
    return hashlib.sha256(("lisa-device-v1:" + guid).encode()).hexdigest()

def _jwk(key) -> dict:
    n = key.public_key().public_numbers()
    return {"kty": "EC", "crv": "P-256", "x": _b64(n.x.to_bytes(32, "big")),
            "y": _b64(n.y.to_bytes(32, "big"))}

def _public_key(jwk: dict):
    if not isinstance(jwk, dict) or jwk.get("kty") != "EC" or jwk.get("crv") != "P-256" or "d" in jwk:
        raise ValueError("Invalid public key.")
    x, y = _unb64(jwk["x"]), _unb64(jwk["y"])
    if len(x) != 32 or len(y) != 32:
        raise ValueError("Invalid public key.")
    return ec.EllipticCurvePublicNumbers(int.from_bytes(x, "big"), int.from_bytes(y, "big"), ec.SECP256R1()).public_key()

def _device_id(jwk: dict) -> str:
    canonical = json.dumps({k: jwk[k] for k in ("crv", "kty", "x", "y")}, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()

def _proof_message(challenge_id, nonce, device, code_hash):
    return "\n".join(("LISA-ACTIVATE-V1", challenge_id, nonce, device, code_hash))

def _verify_device_proof(jwk, proof, message) -> bool:
    try:
        raw = _unb64(proof)
        if len(raw) != 64:
            return False
        signature = encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big"))
        _public_key(jwk).verify(signature, message.encode(), ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False

class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class Activation:
    def __init__(self, directory, base_url=None, *, config=None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.identity_path = self.directory / "activation-device.key"
        self.receipt_path = self.directory / "activation-receipt.jwt"
        self._error = ""
        self._private_key = None
        self.public_jwk = {}
        self.device_id = ""
        self._machine = ""
        if config is None:
            try:
                from core import resource
                path = Path(resource("activation-public.json"))
                if path.stat().st_size > 32768:
                    raise ValueError("Invalid activation configuration.")
                config = json.loads(path.read_text(encoding="utf-8-sig"))
            except Exception:
                config = {}
        self.config = dict(config)
        self.base_url = str(base_url or self.config.get("base_url", "https://lisa-control-center.kitty-ai.workers.dev")).rstrip("/")
        self.purchase_url = str(self.config.get("purchase_url", PURCHASE_URL))
        if urlparse(self.purchase_url).scheme != "https":
            self.purchase_url = PURCHASE_URL
        try:
            self._machine = _machine_binding()
            self._identity()
        except Exception:
            self._error = "Lisa could not unlock this device identity. Keep the original Windows account and activation files; contact Kitty Corp for recovery."

    def _identity(self):
        if not self.identity_path.exists():
            private = ec.generate_private_key(ec.SECP256R1())
            pem = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
            protected = _protect(json.dumps({"v": 1, "machine": self._machine, "private": pem}, separators=(",", ":")).encode())
            try:
                fd = os.open(self.identity_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                pass
            else:
                with os.fdopen(fd, "wb") as f:
                    f.write(protected)
                    f.flush()
                    os.fsync(f.fileno())
        if self.identity_path.stat().st_size > 16384:
            raise ValueError("Invalid device identity.")
        record = json.loads(_protect(self.identity_path.read_bytes(), True))
        if record.get("v") != 1 or record.get("machine") != self._machine:
            raise ValueError("Device identity belongs to another machine.")
        private = serialization.load_pem_private_key(record["private"].encode(), password=None)
        if not isinstance(private, ec.EllipticCurvePrivateKey) or not isinstance(private.curve, ec.SECP256R1):
            raise ValueError("Invalid device key.")
        self._private_key = private
        self.public_jwk = _jwk(private)
        self.device_id = _device_id(self.public_jwk)

    def _verify(self, token):
        if not self._private_key or _machine_binding() != self._machine:
            raise ValueError("Device identity is unavailable.")
        if not isinstance(token, str) or len(token) > 8192 or token.count(".") != 2:
            raise ValueError("Invalid activation receipt.")
        head, body, signature = token.split(".")
        header, claims = json.loads(_unb64(head)), json.loads(_unb64(body))
        if header.get("alg") != "ES256" or header.get("typ") != "JWT" or header.get("kid") != KEY_ID:
            raise ValueError("Invalid activation signature.")
        keys = self.config.get("keys", [])
        jwk = next((key for key in keys if key.get("kid") == KEY_ID), None)
        if jwk is None:
            raise ValueError("Activation verification key is not configured.")
        raw = _unb64(signature)
        if len(raw) != 64:
            raise ValueError("Invalid activation signature.")
        der = encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big"))
        _public_key(jwk).verify(der, (head + "." + body).encode(), ec.ECDSA(hashes.SHA256()))
        now = int(time.time())
        if (claims.get("iss") != ISSUER or claims.get("aud") != AUDIENCE or claims.get("product") != AUDIENCE
            or claims.get("device") != self.device_id or claims.get("machine") != self._machine
            or claims.get("v") != 1 or claims.get("lifetime") is not True
            or not isinstance(claims.get("sub"), str) or not 1 <= len(claims["sub"]) <= 100
            or type(claims.get("iat")) is not int or claims["iat"] < 0 or claims["iat"] > now + 300
            or ("exp" in claims and (type(claims["exp"]) is not int or claims["exp"] <= now))):
            raise ValueError("Activation receipt does not belong to this device.")
        return claims

    def valid(self) -> bool:
        try:
            if self.receipt_path.stat().st_size > 8192:
                return False
            self._verify(self.receipt_path.read_text(encoding="utf-8").strip())
            return True
        except Exception:
            return False

    def status(self) -> dict:
        active = self.valid()
        return {"active": active, "label": "Activated on this device" if active else "Activation required",
                "purchase_url": self.purchase_url, "offline_allowed": active, "error": self._error}

    def _request(self, path, body):
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise RuntimeError("Lisa activation requires its secure HTTPS service.")
        data = json.dumps(body, separators=(",", ":")).encode()
        req = request.Request(self.base_url + path, data=data, method="POST",
                              headers={"Content-Type": "application/json", "User-Agent": "LISA/2.2 Activation"})
        try:
            with request.build_opener(_NoRedirect()).open(req, timeout=15) as response:
                raw = response.read(32769)
                if len(raw) > 32768:
                    raise RuntimeError("Activation service returned an invalid response.")
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise RuntimeError("Activation service returned an invalid response.")
                return result
        except error.HTTPError as e:
            messages = {400: "This code cannot activate Lisa on this device. Check the code or contact Kitty Corp.",
                        429: "Too many activation attempts. Please wait before trying again.",
                        503: "Lisa activation is temporarily unavailable. Please try again later."}
            raise RuntimeError(messages.get(e.code, "Lisa activation could not complete. Please try again later.")) from None
        except (error.URLError, TimeoutError, OSError):
            raise RuntimeError("Connect to the internet for first activation. Offline use works after activation.") from None

    def _submit(self, operation, code_hash=""):
        if self._private_key is None:
            raise RuntimeError(self._error or "Device identity is unavailable.")
        challenge_body = {"operation": operation, "public_jwk": self.public_jwk, "machine": self._machine}
        if operation == "redeem":
            challenge_body["code_hash"] = code_hash
        challenge = self._request("/api/license/challenge", challenge_body)
        cid, nonce = challenge.get("challenge_id"), challenge.get("nonce")
        if (not isinstance(cid, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,80}", cid)
            or not isinstance(nonce, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", nonce)
            or type(challenge.get("expires_at")) is not int or challenge["expires_at"] <= int(time.time())):
            raise ValueError("Activation service returned an invalid challenge.")
        message = _proof_message(cid, nonce, self.device_id, code_hash)
        der = self._private_key.sign(message.encode(), ec.ECDSA(hashes.SHA256()))
        r, s = decode_dss_signature(der)
        proof = _b64(r.to_bytes(32, "big") + s.to_bytes(32, "big"))
        result = self._request("/api/license/" + operation, {"challenge_id": cid, "proof": proof})
        receipt = result.get("token")
        self._verify(receipt)
        temp = self.receipt_path.with_name(self.receipt_path.name + "." + uuid.uuid4().hex + ".tmp")
        try:
            temp.write_text(receipt, encoding="utf-8")
            os.chmod(temp, 0o600)
            temp.replace(self.receipt_path)
        finally:
            temp.unlink(missing_ok=True)
        self._error = ""
        return self.status()

    def activate(self, code) -> dict:
        if not isinstance(code, str) or len(code) > 80:
            raise ValueError("Enter the complete Lisa activation code.")
        normalized = code.strip().upper()
        if not re.fullmatch(r"LISA-(?:[A-Z2-7]{5}-){5}[A-Z2-7]{5}", normalized):
            raise ValueError("Enter the complete Lisa activation code.")
        return self._submit("redeem", hashlib.sha256(normalized.encode()).hexdigest())

    def recover(self) -> dict:
        """Reissue a lost receipt using the same protected identity, without the code."""
        return self._submit("recover")
