import json, os, sys, threading, socket, sqlite3, secrets, hmac, time, urllib.parse, webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import webview

BASE = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "InternetVideoke"
BASE.mkdir(parents=True,exist_ok=True)
DB=BASE/"videoke.db"
TOKEN=secrets.token_urlsafe(32)
PORT=8765
ASSETS=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent))/"web"
def db():
 c=sqlite3.connect(DB,timeout=10)
 c.execute("PRAGMA journal_mode=WAL")
 c.execute("CREATE TABLE IF NOT EXISTS songs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, video TEXT NOT NULL, singer TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'queued', created INTEGER NOT NULL)")
 c.execute("CREATE TABLE IF NOT EXISTS settings (k TEXT PRIMARY KEY, v TEXT)")
 c.execute("INSERT OR IGNORE INTO settings VALUES ('pin','123456')")
 c.commit()
 return c
db().close()
def vid(url):
 url=url.strip()
 u=urllib.parse.urlparse(url)
 host=(u.hostname or '').lower()
 v=''
 if host in ('youtube.com','www.youtube.com','m.youtube.com','music.youtube.com'):
  if u.path=='/watch':v=urllib.parse.parse_qs(u.query).get('v',[''])[0]
  elif u.path.startswith('/shorts/') or u.path.startswith('/embed/'):v=u.path.split('/')[2]
 elif host in ('youtu.be','www.youtu.be'):v=u.path.strip('/').split('/')[0]
 if len(v)==11 and all(c.isalnum() or c in '-_' for c in v):return v
 return None
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def send(self,status,data,ctype='application/json'):
  raw=(json.dumps(data).encode() if ctype=='application/json' else data)
  self.send_response(status)
  self.send_header('Content-Type',ctype)
  self.send_header('Cache-Control','no-store')
  self.send_header('X-Content-Type-Options','nosniff')
  self.send_header('Content-Security-Policy',"default-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://i.ytimg.com; script-src 'self' https://www.youtube.com https://s.ytimg.com; style-src 'self' 'unsafe-inline'; img-src 'self' https://i.ytimg.com data:; frame-src https://www.youtube.com https://www.youtube-nocookie.com; connect-src 'self' https://www.youtube.com")
  self.send_header('Content-Length',str(len(raw)))
  self.end_headers();self.wfile.write(raw)
 def getjson(self):
  try:
   n=int(self.headers.get('Content-Length','0'))
   if n>10000:return None
   return json.loads(self.rfile.read(n)) if n else {}
  except Exception:return None
 def authorized(self):
  # Host-only controls: require localhost + token. Remote phones cannot obtain token.
  return self.client_address[0] in ('127.0.0.1','::1') and hmac.compare_digest(self.headers.get('X-Host-Token',''),TOKEN)
 def do_GET(self):
  path=urllib.parse.urlparse(self.path).path
  if path=='/api/list':
   with db() as c:
    rows=c.execute("SELECT id,title,video,singer,status FROM songs WHERE status!='done' ORDER BY id").fetchall()
   self.send(200,[dict(zip(['id','title','video','singer','status'],r)) for r in rows]);return
  if path=='/api/info':
   self.send(200,{'host':self.client_address[0] in ('127.0.0.1','::1'),'token':TOKEN if self.client_address[0] in ('127.0.0.1','::1') else '', 'ip':localip()});return
  if path in ('/','/remote'):
   f=ASSETS/('index.html' if path=='/' else 'remote.html')
   self.send(200,f.read_bytes(),'text/html; charset=utf-8');return
  if path in ('/app.js','/style.css','/menu.js','/logo.svg'):
   f=ASSETS/path[1:]
   self.send(200,f.read_bytes(),'application/javascript' if path.endswith('.js') else ('image/svg+xml' if path.endswith('.svg') else 'text/css'));return
  self.send(404,{'error':'Not found'})
 def do_POST(self):
  path=urllib.parse.urlparse(self.path).path
  d=self.getjson()
  if not isinstance(d,dict):self.send(400,{'error':'Invalid request'});return
  if path=='/api/add':
   title=str(d.get('title','')).strip()[:160];v=vid(str(d.get('video','')))
   singer=str(d.get('singer','')).strip()[:80]
   if not title or not v:self.send(400,{'error':'Enter title and valid YouTube link'});return
   with db() as c:c.execute("INSERT INTO songs(title,video,singer,status,created) VALUES (?,?,?,'queued',?)",(title,v,singer,int(time.time())))
   self.send(200,{'ok':True});return
  if path=='/api/done':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   try:songid=int(d.get('id'))
   except (ValueError,TypeError):self.send(400,{'error':'Invalid ID'});return
   with db() as c:c.execute("UPDATE songs SET status='done' WHERE id=?",(songid,))
   self.send(200,{'ok':True});return
  if path=='/api/clear':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   with db() as c:c.execute("UPDATE songs SET status='done' WHERE status!='done'")
   self.send(200,{'ok':True});return
  self.send(404,{'error':'Not found'})
def localip():
 try:
  s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80));ip=s.getsockname()[0];s.close();return ip
 except OSError:return '127.0.0.1'
def main():
 global PORT
 for port in (8765,8766,8767):
  try:
   server=ThreadingHTTPServer(('0.0.0.0',port),Handler);PORT=port;break
  except OSError:continue
 else:raise RuntimeError("Ports 8765-8767 are in use.")
 threading.Thread(target=server.serve_forever,daemon=True).start()
 url=f'http://127.0.0.1:{PORT}/'
 webview.create_window('Internet Videoke - Windows',url,width=1300,height=800,min_size=(850,600))
 webview.start(debug=False)
 server.shutdown()
if __name__=='__main__':main()
