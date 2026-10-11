"""Read-only loopback asset server. Only the bundled suite can be served."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import mimetypes,threading
from urllib.parse import unquote,urlsplit
class SceneServer:
 def __init__(self,root):
  self.root=Path(root).resolve()
  root=self.root
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*_):pass
   def do_GET(self):
    rel=unquote(urlsplit(self.path).path).lstrip("/") or "runtime/room.html"
    path=(root/rel).resolve()
    if not path.is_relative_to(root) or path.suffix.lower() not in {".html",".js",".css",".json",".glb",".png",".webp",".jpg",".ico",".woff2"} or not path.is_file():
     self.send_error(404);return
    self.send_response(200);self.send_header("Content-Type",{".js":"text/javascript",".glb":"model/gltf-binary"}.get(path.suffix,mimetypes.guess_type(str(path))[0] or "application/octet-stream"));self.send_header("X-Content-Type-Options","nosniff");self.send_header("Cache-Control","no-store");self.end_headers()
    try:
     with path.open("rb") as f:
      while b:=f.read(262144):self.wfile.write(b)
    except (BrokenPipeError,ConnectionResetError):pass
  self.http=ThreadingHTTPServer(("127.0.0.1",0),Handler);self.http.daemon_threads=True
  self.url=f"http://127.0.0.1:{self.http.server_port}/runtime/room.html"
  self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
 def close(self):
  self.http.shutdown();self.http.server_close()
