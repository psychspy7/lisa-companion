"""Small reviewed PC tools. Model output never becomes a shell command."""
import ipaddress
import re
import subprocess
import urllib.parse
import webbrowser

APPS = {"calculator": ["calc.exe"], "notepad": ["notepad.exe"], "explorer": ["explorer.exe"]}


def public_https(value):
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443):
        raise ValueError("Use a public HTTPS address without login details.")
    host=parsed.hostname.lower()
    if host == "localhost" or host.endswith((".local", ".localhost", ".internal")) or "." not in host:
        raise ValueError("Local network addresses are unsupported.")
    try:
        address=ipaddress.ip_address(host)
    except ValueError:
        address=None
    if address is not None and not address.is_global:
        raise ValueError("Local network addresses are unsupported.")
    if any(c.isspace() or ord(c)<32 for c in value):
        raise ValueError("Invalid URL.")
    return value


def validate_action(action):
    if not isinstance(action,dict) or not isinstance(action.get("value"),str):
        raise ValueError("Unsupported action.")
    kind,value=action.get("type"),action["value"]
    if kind=="open_app" and value in (*APPS,"browser"):
        return kind,value
    if kind=="open_url": return kind,public_https(value)
    if kind in ("create_note","copy_text") and 0<len(value)<=8000:
        return kind,value
    raise ValueError("This action is unsupported. Lisa can open known apps or HTTPS pages, save a note, and copy text.")


def explicit_local_action(text):
    match=re.fullmatch(r"\s*(?:please\s+)?(?:open|launch|start)\s+(?:the\s+)?(calculator|notepad|explorer|browser)\s*[.!]?\s*",text,re.I)
    return {"type":"open_app","value":match[1].lower()} if match else None


def open_target(kind,value):
    validate_action({"type":kind,"value":value})
    if kind=="open_url" or value=="browser":
        if not webbrowser.open(value if kind=="open_url" else "https://www.google.com"):
            raise RuntimeError("Windows could not open the browser.")
    elif kind=="open_app":
        subprocess.Popen(APPS[value],shell=False)
    else:
        raise ValueError("This action needs the app's file or clipboard dialog.")
