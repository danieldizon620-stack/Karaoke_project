import json, os, sys, threading, socket, sqlite3, secrets, hmac, time, urllib.parse, webbrowser, mimetypes, re, zipfile, io, hashlib
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import webview

BASE = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "InternetVideoke"
BASE.mkdir(parents=True,exist_ok=True)
DB=BASE/"videoke.db"
TOKEN=secrets.token_urlsafe(32)
LIBRARY_EXT={".mp3",".mp4",".m4v",".webm",".cdg",".zip"}
scan_lock=threading.Lock()
PORT=8765
ASSETS=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent))/"web"
def db():
 c=sqlite3.connect(DB,timeout=10)
 c.execute("PRAGMA journal_mode=WAL")
 c.execute("CREATE TABLE IF NOT EXISTS songs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, video TEXT NOT NULL, singer TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'queued', created INTEGER NOT NULL)")
 c.execute("CREATE TABLE IF NOT EXISTS library (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL UNIQUE, title TEXT NOT NULL, artist TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT 'Other', kind TEXT NOT NULL, mtime REAL NOT NULL, size INTEGER NOT NULL)")
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
def scan_library():
 with scan_lock:
  with db() as c:
   roots=[r[0] for r in c.execute("SELECT v FROM settings WHERE k='song_folder'").fetchall()]
   if not roots:return {'count':0,'added':0,'folder':''}
   root=Path(roots[0]).expanduser()
   if not root.is_dir():return {'count':0,'added':0,'folder':str(root),'error':'Folder does not exist'}
   seen=set();added=0
   for directory,_,names in os.walk(root):
    for name in names:
     f=Path(directory)/name
     ext=f.suffix.lower()
     if ext not in LIBRARY_EXT or ext=='.cdg':continue
     if ext=='.mp3' and not f.with_suffix('.cdg').is_file():continue
     if ext=='.zip':
      try:
       with zipfile.ZipFile(f) as z:
        entries=[n.lower() for n in z.namelist()]
        if not any(n.endswith('.cdg') for n in entries) or not any(n.endswith('.mp3') for n in entries):continue
      except (OSError,zipfile.BadZipFile):continue
     try:st=f.stat()
     except OSError:continue
     path=str(f.resolve());seen.add(path)
     stem=f.stem.replace('_',' ').strip()
     bits=re.split(r'\s+-\s+',stem,maxsplit=1)
     artist,title=(bits[0],bits[1]) if len(bits)==2 else ('',stem)
     category=next((part for part in f.relative_to(root).parts[:-1] if part),'Other')
     cur=c.execute('INSERT OR IGNORE INTO library(path,title,artist,category,kind,mtime,size) VALUES (?,?,?,?,?,?,?)',(path,title,artist,category,ext[1:],st.st_mtime,st.st_size))
     added+=cur.rowcount
     c.execute('UPDATE library SET mtime=?,size=? WHERE path=?',(st.st_mtime,st.st_size,path))
   old=c.execute('SELECT id,path FROM library').fetchall()
   for id_,path in old:
    if path not in seen:c.execute('DELETE FROM library WHERE id=?',(id_,))
   return {'count':len(seen),'added':added,'folder':str(root)}
def choose_folder():
 try:
  import tkinter as tk
  from tkinter import filedialog
  root=tk.Tk();root.withdraw();root.attributes('-topmost',True)
  folder=filedialog.askdirectory(title='Select your Karaoke Songs folder')
  root.destroy()
  return folder
 except Exception:return ''
def library_path(id_):
 with db() as c:row=c.execute('SELECT path,kind FROM library WHERE id=?',(id_,)).fetchone()
 return row
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
  if path=='/api/library':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   q=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0][:120]
   with db() as c:
    if q:
     like='%'+q.replace('%','\%').replace('_','\_')+'%'
     rows=c.execute("SELECT id,title,artist,category,kind FROM library WHERE title LIKE ? ESCAPE '\\' OR artist LIKE ? ESCAPE '\\' OR category LIKE ? ESCAPE '\\' OR printf('%05d',id) LIKE ? ORDER BY title LIMIT 400",(like,like,like,like)).fetchall()
    else:rows=c.execute('SELECT id,title,artist,category,kind FROM library ORDER BY title LIMIT 400').fetchall()
   self.send(200,[dict(zip(['id','title','artist','category','kind'],r)) for r in rows]);return
  if path=='/api/library_status':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   with db() as c:
    folder=c.execute("SELECT v FROM settings WHERE k='song_folder'").fetchone()
    count=c.execute('SELECT COUNT(*) FROM library').fetchone()[0]
   self.send(200,{'folder':folder[0] if folder else '', 'count':count});return
  if path.startswith('/api/media/'):
   if not self.authorized():self.send(403,{'error':'Host only'});return
   try:id_=int(path.split('/')[-1])
   except ValueError:self.send(400,{'error':'Bad song ID'});return
   row=library_path(id_)
   if not row:self.send(404,{'error':'Song not found'});return
   file,kind=row
   if kind=='zip':
    self.send(415,{'error':'ZIP playback requires extracting the MP3+G pair to the song folder'});return
   f=Path(file)
   if not f.is_file():self.send(404,{'error':'File missing'});return
   if kind=='mp3' and urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('lyrics')==['1']:
    f=f.with_suffix('.cdg')
   if not f.is_file():self.send(404,{'error':'Lyrics missing'});return
   mime='application/octet-stream' if f.suffix.lower()=='.cdg' else (mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
   size=f.stat().st_size;range_header=self.headers.get('Range','')
   m=re.match(r'bytes=(\d+)-(\d*)$',range_header)
   start=int(m.group(1)) if m else 0;end=min(int(m.group(2)),size-1) if m and m.group(2) else size-1
   if start>=size or end<start:self.send_response(416);self.end_headers();return
   self.send_response(206 if m else 200);self.send_header('Content-Type',mime);self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1))
   if m:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
   self.end_headers()
   try:
    with f.open('rb') as stream:
     stream.seek(start);left=end-start+1
     while left>0:
      chunk=stream.read(min(65536,left))
      if not chunk:break
      self.wfile.write(chunk);left-=len(chunk)
   except (BrokenPipeError,ConnectionResetError):pass
   return
  if path=='/api/list':
   with db() as c:
    rows=c.execute("SELECT id,title,video,singer,status FROM songs WHERE status!='done' ORDER BY id").fetchall()
   self.send(200,[dict(zip(['id','title','video','singer','status'],r)) for r in rows]);return
  if path=='/api/info':
   self.send(200,{'host':self.client_address[0] in ('127.0.0.1','::1'),'token':TOKEN if self.client_address[0] in ('127.0.0.1','::1') else '', 'ip':localip()});return
  if path in ('/','/remote'):
   f=ASSETS/('index.html' if path=='/' else 'remote.html')
   self.send(200,f.read_bytes(),'text/html; charset=utf-8');return
  if path in ('/app.js','/style.css','/menu.js','/logo.svg','/customize.js','/starter_songs.json','/library.js'):
   f=ASSETS/path[1:]
   self.send(200,f.read_bytes(),'application/javascript' if path.endswith('.js') else ('image/svg+xml' if path.endswith('.svg') else ('application/json' if path.endswith('.json') else 'text/css')));return
  self.send(404,{'error':'Not found'})
 def do_POST(self):
  path=urllib.parse.urlparse(self.path).path
  d=self.getjson()
  if not isinstance(d,dict):self.send(400,{'error':'Invalid request'});return
  if path=='/api/choose_folder':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   folder=choose_folder()
   if not folder:self.send(200,{'cancelled':True});return
   with db() as c:c.execute("INSERT OR REPLACE INTO settings(k,v) VALUES ('song_folder',?)",(folder,))
   self.send(200,scan_library());return
  if path=='/api/scan':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   self.send(200,scan_library());return
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
