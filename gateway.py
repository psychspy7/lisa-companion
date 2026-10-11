"""Owner-only cloud connection; provider keys never enter the room renderer."""
import base64,hashlib,io,json,threading,time,urllib.request,urllib.error,urllib.parse,wave
from pathlib import Path
from core import ApiError,dpapi,resource
class StrictRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if urllib.parse.urlsplit(newurl).scheme!='https' or urllib.parse.urlsplit(newurl).netloc!=urllib.parse.urlsplit(req.full_url).netloc:raise ApiError('Lisa rejected an unexpected redirect.')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
class Gateway:
 def __init__(self,directory):
  self.path=Path(directory)/"google-session.key";self.lock=threading.RLock();self.session={}
  cfg=json.loads(resource("control-center.json").read_text());self.url=cfg["url"].rstrip("/")
  p=urllib.parse.urlsplit(self.url)
  if p.scheme!="https" or p.hostname!="lisa-control-center.kitty-ai.workers.dev" or p.username or p.password:raise ValueError("Invalid Lisa backend")
  if self.path.exists():
   try:self.session=json.loads(dpapi(self.path.read_bytes(),True))
   except (OSError,ValueError,RuntimeError):self.session={}
 @property
 def connected(self):return bool(self.session.get("refresh_token"))
 def save(self,data):
  with self.lock:
   self.session={**data,"expires_at":time.time()+int(data.get("expires_in",3600))-90}
   temp=self.path.with_suffix(".tmp");temp.write_bytes(dpapi(json.dumps(self.session).encode()));temp.replace(self.path)
 def logout(self):
  with self.lock:self.session={};self.path.unlink(missing_ok=True)
 def token(self):
  with self.lock:
   if not self.connected:raise ApiError("Link Lisa to your Google account in the menu.")
   if time.time()<self.session.get("expires_at",0):return self.session["id_token"]
   data=self._http("https://securetoken.googleapis.com/v1/token?key="+urllib.parse.quote(self.session["api_key"]),urllib.parse.urlencode({"grant_type":"refresh_token","refresh_token":self.session["refresh_token"]}).encode(),"application/x-www-form-urlencoded")
   self.save({**self.session,**json.loads(data)});return self.session["id_token"]
 def _http(self,url,body=None,content="application/json",headers=None,method=None):
  req=urllib.request.Request(url,data=body,headers={"Content-Type":content,"User-Agent":"LISA/1.10.0",**(headers or {})},method=method or ("POST" if body is not None else "GET"))
  try:
   with urllib.request.build_opener(StrictRedirect()).open(req,timeout=65) as r:
    if urllib.parse.urlsplit(r.geturl()).netloc!=urllib.parse.urlsplit(url).netloc:raise ApiError("Lisa rejected an unexpected redirect.")
    raw=r.read(12_000_001)
    if len(raw)>12_000_000:raise ApiError("Lisa returned a response that was too large.")
    return raw,dict(r.headers) if False else raw
  except urllib.error.HTTPError as e:
   try:message=json.loads(e.read(16000)).get("error","Lisa connection failed.")
   except (ValueError,UnicodeError):message="Lisa connection failed (HTTP "+str(e.code)+")."
   raise ApiError(str(message)[:2000],status=e.code,category="auth" if e.code in (401,403) else "service") from None
  except (OSError,urllib.error.URLError):raise ApiError("Could not reach the Lisa control center. Check your internet connection.") from None
 def call(self,path,body=None,raw=None,method=None,authenticated=True):
  headers={"Authorization":"Bearer "+self.token()} if authenticated else {}
  payload=raw if raw is not None else json.dumps(body,ensure_ascii=False).encode() if body is not None else None
  return self._http(self.url+path,payload,"audio/wav" if raw is not None else "application/json",headers,method)
 def json(self,path,body=None,**kwargs):return json.loads(self.call(path,body,**kwargs))
 def start(self):
  import secrets
  verifier=secrets.token_urlsafe(48);data=self.json("/api/device/start",{"challenge":hashlib.sha256(verifier.encode()).hexdigest()},authenticated=False);data["verifier"]=verifier;return data
 def poll(self,device):
  data=self.json("/api/device/poll",{"device_id":device["device_id"],"verifier":device["verifier"]},authenticated=False)
  if data.get("pending"):return False
  self.save(data);return True
 def config(self):return self.json("/api/config")
 def chat(self,text,history,memories):
  from providers import validate_reply
  return validate_reply(self.json("/api/chat",{"message":text,"history":history[-16:],"memories":memories[-50:]}))
 def transcribe(self,wav):return self.json("/api/transcribe",raw=wav)["text"]
 def speech(self,text,mood):
  # The gateway normalizes both providers to a real WAV.
  return self.call("/api/tts",{"text":text,"mood":mood})
 def migrate(self,keys,settings):
  cfg=self.config();existing={p["id"] for p in cfg["providers"] if p["configured"]};moved=[]
  for p,credential in keys.items():
   if p in existing:continue
   key=credential.get()
   if key:self.json("/api/admin/providers/"+p,{"key":key},method="PUT");moved.append(p)
  if moved:self.json("/api/admin/settings",settings)
  return moved
 def submit(self,image,mood,green_screen=False):
  from motion import stage_image,motion_prompt
  return self.json("/api/vidu/generate",{"image":stage_image(image,green_screen),"prompt":motion_prompt(mood,green_screen)})["task_id"]
 def result(self,task_id):return self.json("/api/vidu/tasks/"+urllib.parse.quote(task_id,safe=""))
