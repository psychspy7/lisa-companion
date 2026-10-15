"""Ephemeral activation checks do not read user data or use live credentials."""
import base64, json, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from activation import Activation
def b64(data): return base64.urlsafe_b64encode(data).rstrip(b"=").decode()
def public(key,kid=None):
    n=key.public_key().public_numbers()
    r={"kty":"EC","crv":"P-256","x":b64(n.x.to_bytes(32,"big")),"y":b64(n.y.to_bytes(32,"big"))}
    if kid:r["kid"]=kid
    return r
def token(key,claims,kid="lisa-license-2026-22"):
    h=b64(json.dumps({"alg":"ES256","typ":"JWT","kid":kid},separators=(",",":")).encode())
    p=b64(json.dumps(claims,separators=(",",":")).encode())
    r,s=decode_dss_signature(key.sign((h+"."+p).encode(),ec.ECDSA(hashes.SHA256())))
    return h+"."+p+"."+b64(r.to_bytes(32,"big")+s.to_bytes(32,"big"))
class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.directory=Path(self.tmp.name)
        self.signing=ec.generate_private_key(ec.SECP256R1())
        self.config={"base_url":"https://example.invalid","issuer":"lisa-kittycorp","audience":"lisa-desktop",
          "purchase_url":"https://kittycorp.vercel.app/","keys":[public(self.signing,"lisa-license-2026-22")]}
        self.protect=patch("activation._protect",lambda value,decrypt=False:b"protected:"+value if not decrypt else value.removeprefix(b"protected:"))
        self.machine=patch("activation._machine_binding",return_value="a"*64)
        self.protect.start();self.machine.start()
        self.addCleanup(self.protect.stop);self.addCleanup(self.machine.stop);self.addCleanup(self.tmp.cleanup)
        self.a=Activation(self.directory,config=self.config)
    def claims(self,**changes):
        value={"iss":"lisa-kittycorp","aud":"lisa-desktop","sub":"license-test","iat":int(time.time()),
          "v":1,"device":self.a.device_id,"machine":"a"*64,"product":"lisa-desktop","lifetime":True}
        value.update(changes);return value
    def save(self,**changes):self.a.receipt_path.write_text(token(self.signing,self.claims(**changes)),encoding="utf-8")
    def test_signed_entitlement_and_public_status(self):
        self.assertFalse(self.a.valid());self.save();self.assertTrue(self.a.valid())
        self.assertTrue(self.a.status()["active"]);self.assertNotIn(self.a.device_id,json.dumps(self.a.status()))
        self.assertNotIn("private",json.dumps(self.a.status()))
    def test_tampered_wrong_audience_key_future_or_nonlifetime_receipts_reject(self):
        for changes in ({"aud":"elsewhere"},{"iat":int(time.time())+7200},{"lifetime":False}):
            self.save(**changes);self.assertFalse(self.a.valid())
        self.save();parts=self.a.receipt_path.read_text().split(".")
        parts[1]=b64(json.dumps(self.claims(sub="attacker")).encode())
        self.a.receipt_path.write_text(".".join(parts));self.assertFalse(self.a.valid())
        self.a.receipt_path.write_text(token(ec.generate_private_key(ec.SECP256R1()),self.claims()));self.assertFalse(self.a.valid())
    def test_copied_receipt_or_machine_reject(self):
        self.save();other=Activation(self.directory/"different",config=self.config)
        other.receipt_path.write_text(self.a.receipt_path.read_text());self.assertFalse(other.valid())
        with patch("activation._machine_binding",return_value="b"*64):self.assertFalse(Activation(self.directory,config=self.config).valid())
    def test_activation_proof_and_recovery_keep_identity(self):
        requests=[]
        def request(path,body):
            requests.append((path,body))
            if path.endswith("challenge"):return {"challenge_id":"challenge-test","nonce":"z"*43,"expires_at":int(time.time())+300}
            from activation import _verify_device_proof
            message="LISA-ACTIVATE-V1\nchallenge-test\n"+"z"*43+"\n"+self.a.device_id+"\n"+(requests[-2][1].get("code_hash") or "")
            self.assertTrue(_verify_device_proof(self.a.public_jwk,body["proof"],message))
            return {"token":token(self.signing,self.claims())}
        with patch.object(self.a,"_request",side_effect=request):
            self.assertTrue(self.a.activate("LISA-ABCDE-FGHIJ-KLMNO-PQRST-UVWXY-Z2345")["active"])
            self.a.receipt_path.unlink();self.assertTrue(self.a.recover()["active"])
        self.assertEqual(requests[0][1]["operation"],"redeem");self.assertEqual(requests[2][1]["operation"],"recover")
        self.assertNotIn("ABCDE",json.dumps(requests))
    def test_invalid_response_or_code_never_saves_receipt(self):
        with patch.object(self.a,"_request") as request:
            with self.assertRaises(ValueError):self.a.activate("bad")
            request.assert_not_called()
        def server(path,body):
            return {"challenge_id":"c","nonce":"z"*43,"expires_at":int(time.time())+300} if path.endswith("challenge") else {"token":"bad"}
        with patch.object(self.a,"_request",side_effect=server):
            with self.assertRaises(ValueError):self.a.activate("LISA-ABCDE-FGHIJ-KLMNO-PQRST-UVWXY-Z2345")
        self.assertFalse(self.a.receipt_path.exists())
    def test_identity_corruption_fails_closed_and_preserves_receipt(self):
        self.save();self.a.identity_path.write_bytes(b"invalid")
        self.assertFalse(Activation(self.directory,config=self.config).valid());self.assertTrue(self.a.receipt_path.exists())
if __name__=="__main__":unittest.main()
