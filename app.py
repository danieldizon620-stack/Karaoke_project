DEFAULT_YOUTUBE_API_KEY = 'AIzaSyDWBXrmebCs6TMViQOVdvm14KE1zcgTFKA'
import urllib.request, json, shutil, os, sys, threading, socket, sqlite3, secrets, hmac, time, urllib.parse, webbrowser, mimetypes, re, zipfile, io, hashlib
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import webview

BASE = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "DannyboisKaraoke"
BASE.mkdir(parents=True,exist_ok=True)
DEFAULT_SONGS=BASE/"Songs"
DEFAULT_SONGS.mkdir(exist_ok=True)
DB=BASE/"videoke.db"
TOKEN=secrets.token_urlsafe(32)
REMOTE_PIN=os.getenv('DANNYBOI_REMOTE_PIN') or ''.join(str(secrets.randbelow(10)) for _ in range(6))
REMOTE_PORT=8877
REMOTE_QUEUE_LOCK=threading.Lock()

LIBRARY_EXT={".mp3",".mp4",".m4v",".webm",".cdg",".zip"}
scan_lock=threading.Lock()
PORT=8765
ASSETS=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent))/"web"
def db():
 c=sqlite3.connect(DB,timeout=10)
 c.execute("PRAGMA journal_mode=WAL")
 c.execute("CREATE TABLE IF NOT EXISTS songs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, video TEXT NOT NULL, singer TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'queued', created INTEGER NOT NULL)")
 c.execute("CREATE TABLE IF NOT EXISTS library (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL UNIQUE, title TEXT NOT NULL, artist TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT 'Other', kind TEXT NOT NULL, mtime REAL NOT NULL, size INTEGER NOT NULL)")
 c.execute("CREATE TABLE IF NOT EXISTS api_songs (code TEXT PRIMARY KEY, title TEXT NOT NULL, artist TEXT NOT NULL DEFAULT '', language TEXT NOT NULL DEFAULT '', youtube_id TEXT NOT NULL DEFAULT '')")
 c.execute("CREATE TABLE IF NOT EXISTS api_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT NOT NULL, title TEXT NOT NULL, artist TEXT NOT NULL DEFAULT '', youtube_id TEXT NOT NULL DEFAULT '', created INTEGER NOT NULL)")
 c.execute("CREATE TABLE IF NOT EXISTS settings (k TEXT PRIMARY KEY, v TEXT)")
 c.execute("CREATE TABLE IF NOT EXISTS remote_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, artist TEXT NOT NULL DEFAULT '', youtube_id TEXT NOT NULL, created INTEGER NOT NULL)")
 c.execute("INSERT OR IGNORE INTO settings VALUES ('song_folder',?)",(str(DEFAULT_SONGS),))
 c.commit()
 return c
db().close()
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
def import_songs():
 try:
  import tkinter as tk
  from tkinter import filedialog
  root=tk.Tk();root.withdraw();root.attributes('-topmost',True)
  paths=filedialog.askopenfilenames(title='Import legally obtained karaoke songs',filetypes=[('Karaoke songs','*.mp3 *.cdg *.mp4 *.m4v *.webm *.zip'),('All files','*.*')])
  root.destroy()
  if not paths:return {'cancelled':True}
  with db() as c:
   row=c.execute("SELECT v FROM settings WHERE k='song_folder'").fetchone()
  folder=Path(row[0]) if row else DEFAULT_SONGS
  folder.mkdir(parents=True,exist_ok=True)
  added=0;skipped=0
  for source in paths:
   src=Path(source)
   if src.suffix.lower() not in LIBRARY_EXT or not src.is_file():skipped+=1;continue
   dst=folder/src.name
   try:
    if src.resolve()==dst.resolve():skipped+=1;continue
    if dst.exists():skipped+=1;continue
    shutil.copy2(src,dst);added+=1
   except OSError:skipped+=1
  result=scan_library();result.update({'imported':added,'skipped':skipped});return result
 except Exception as e:return {'error':str(e)}
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
  self.send_header('Access-Control-Allow-Origin','null')
  self.send_header('X-Content-Type-Options','nosniff')
  self.send_header('Content-Security-Policy',"default-src 'self' data: blob:; script-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://www.google.com; frame-src https://www.youtube.com https://www.youtube-nocookie.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://i.ytimg.com https://*.ytimg.com; media-src 'self' blob:; connect-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://*.googlevideo.com")
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
 def remote_auth(self):
  return hmac.compare_digest(self.headers.get('X-Remote-PIN',''),REMOTE_PIN)
 def do_GET(self):
  path=urllib.parse.urlparse(self.path).path
  if path=='/remote/health':
   self.send(200,{'app':'dannyboi Karaoke','remote':True});return
  if path=='/api/remote/queue':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   with REMOTE_QUEUE_LOCK:
    with db() as c:rows=c.execute('SELECT id,title,artist,youtube_id FROM remote_queue ORDER BY id').fetchall()
   self.send(200,{'queue':[dict(zip(('id','title','artist','videoId'),r)) for r in rows]});return
  if path=='/remote/queue':
   if not self.remote_auth():self.send(403,{'error':'Wrong pairing PIN'});return
   with REMOTE_QUEUE_LOCK:
    with db() as c:rows=c.execute('SELECT id,title,artist,youtube_id FROM remote_queue ORDER BY id').fetchall()
   self.send(200,{'queue':[dict(zip(('id','title','artist','videoId'),r)) for r in rows]});return
  if path=='/remote/search':
   if not self.remote_auth():self.send(403,{'error':'Wrong pairing PIN'});return
   q=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0][:120]
   if not q:self.send(400,{'error':'Search text required'});return
   key=os.getenv('YOUTUBE_DATA_API_KEY','') or os.getenv('YOUTUBE_API_KEY','')
   if not key:
    with db() as c:row=c.execute("SELECT v FROM settings WHERE k='youtube_api_key'").fetchone()
    key=row[0] if row else ''
   if not key:key=DEFAULT_YOUTUBE_API_KEY
   if not key:self.send(503,{'error':'Configure YouTube API on Windows first'});return
   url='https://www.googleapis.com/youtube/v3/search?'+urllib.parse.urlencode({'part':'snippet','type':'video','maxResults':12,'q':q+' karaoke','key':key})
   try:
    with urllib.request.urlopen(url,timeout=12) as response:data=json.load(response)
    self.send(200,{'results':[{'videoId':x.get('id',{}).get('videoId',''),'title':x.get('snippet',{}).get('title',''),'channel':x.get('snippet',{}).get('channelTitle','')} for x in data.get('items',[])]})
   except Exception:self.send(502,{'error':'YouTube search failed: check API key, quota and internet'})
   return
  if path=='/api/songs/search':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   q=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0][:120]
   with db() as c:
    like='%'+q.replace('%',r'\%').replace('_',r'\_')+'%'
    rows=c.execute("SELECT code,title,artist,language,youtube_id FROM api_songs WHERE title LIKE ? ESCAPE '\' OR artist LIKE ? ESCAPE '\' OR code LIKE ? ESCAPE '\' OR language LIKE ? ESCAPE '\' ORDER BY title LIMIT 150",(like,like,like,like)).fetchall()
   self.send(200,{'songs':[dict(zip(('code','title','artist','language','youtube_id'),r)) for r in rows]});return
  if path.startswith('/api/songs/'):
   if not self.authorized():self.send(403,{'error':'Host only'});return
   code=urllib.parse.unquote(path[len('/api/songs/'):])
   with db() as c:row=c.execute('SELECT code,title,artist,language,youtube_id FROM api_songs WHERE code=?',(code,)).fetchone()
   self.send(200,dict(zip(('code','title','artist','language','youtube_id'),row))) if row else self.send(404,{'error':'Song not found'});return
  if path=='/api/queue':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   with db() as c:rows=c.execute('SELECT id,code,title,artist,youtube_id FROM api_queue ORDER BY id').fetchall()
   self.send(200,{'queue':[dict(zip(('id','code','title','artist','youtube_id'),r)) for r in rows]});return
  if path=='/api/youtube/status':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   with db() as c:row=c.execute("SELECT v FROM settings WHERE k='youtube_api_key'").fetchone()
   self.send(200,{'configured':bool(os.getenv('YOUTUBE_DATA_API_KEY') or os.getenv('YOUTUBE_API_KEY') or (row and row[0]) or DEFAULT_YOUTUBE_API_KEY)});return
  if path=='/api/youtube/search':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   key=os.getenv('YOUTUBE_DATA_API_KEY','') or os.getenv('YOUTUBE_API_KEY','')
   if not key:
    with db() as c:
     row=c.execute("SELECT v FROM settings WHERE k='youtube_api_key'").fetchone()
     key=row[0] if row else ''
   if not key:key=DEFAULT_YOUTUBE_API_KEY
   if not key:self.send(503,{'error':'YouTube API key is not configured. Enter it when prompted.'});return
   q=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0][:120]
   if not q:self.send(400,{'error':'Missing q'});return
   url='https://www.googleapis.com/youtube/v3/search?'+urllib.parse.urlencode({'part':'snippet','type':'video','maxResults':15,'q':q,'key':key})
   try:
    with urllib.request.urlopen(url,timeout=10) as response:data=json.load(response)
    self.send(200,{'results':[{'videoId':x.get('id',{}).get('videoId',''),'title':x.get('snippet',{}).get('title',''),'channel':x.get('snippet',{}).get('channelTitle','')} for x in data.get('items',[])]})
   except Exception:self.send(502,{'error':'YouTube search unavailable; check API key, quota and connection'})
   return
  if path=='/api/library':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   q=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0][:120]
   with db() as c:
    if q:
     like='%'+q.replace('%',r'\%').replace('_',r'\_')+'%'
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
  if path=='/api/info':
   self.send(200,{'host':self.client_address[0] in ('127.0.0.1','::1'),'token':TOKEN if self.client_address[0] in ('127.0.0.1','::1') else '', 'ip':localip(),'remote_port':REMOTE_PORT,'remote_pin':REMOTE_PIN if self.client_address[0] in ('127.0.0.1','::1') else ''});return
  if path=='/':
   f=ASSETS/'index.html'
   self.send(200,f.read_bytes(),'text/html; charset=utf-8');return
  if path in ('/app.js','/style.css','/menu.js','/logo.svg','/customize.js','/library.js','/online.js','/videoke_api.js','/simple.js','/dannyboi_logo.png'):
   f=ASSETS/path[1:]
   self.send(200,f.read_bytes(),'image/png' if path.endswith('.png') else ('application/javascript' if path.endswith('.js') else ('image/svg+xml' if path.endswith('.svg') else 'text/css')));return
  self.send(404,{'error':'Not found'})
 def do_POST(self):
  path=urllib.parse.urlparse(self.path).path
  d=self.getjson()
  if not isinstance(d,dict):self.send(400,{'error':'Invalid request'});return
  if path=='/remote/queue':
   if not self.remote_auth():self.send(403,{'error':'Wrong pairing PIN'});return
   vid=str(d.get('videoId','')).strip();title=str(d.get('title','')).strip()[:250];artist=str(d.get('artist','')).strip()[:120]
   if not re.fullmatch(r'[A-Za-z0-9_-]{11}',vid) or not title:self.send(400,{'error':'Invalid song or video ID'});return
   with REMOTE_QUEUE_LOCK:
    with db() as c:
     existing=c.execute('SELECT id FROM remote_queue WHERE youtube_id=?',(vid,)).fetchone()
     if existing:self.send(200,{'id':existing[0],'already_queued':True});return
     cur=c.execute('INSERT INTO remote_queue(title,artist,youtube_id,created) VALUES (?,?,?,?)',(title,artist,vid,int(time.time())))
   self.send(201,{'id':cur.lastrowid,'added':True});return
  if path=='/api/youtube/key':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   key=str(d.get('key','')).strip()
   if key and (len(key)>160 or not re.fullmatch(r'[A-Za-z0-9_-]+',key)):
    self.send(400,{'error':'Invalid API key format'});return
   with db() as c:c.execute("INSERT OR REPLACE INTO settings(k,v) VALUES ('youtube_api_key',?)",(key,))
   self.send(200,{'saved':True,'configured':bool(key)});return
  if path=='/api/queue':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   code=str(d.get('code',''))[:120]
   if not code:self.send(400,{'error':'Song code required'});return
   with db() as c:
    row=c.execute('SELECT title,artist,youtube_id FROM api_songs WHERE code=?',(code,)).fetchone()
    if not row:self.send(404,{'error':'Song code not found'});return
    cur=c.execute('INSERT INTO api_queue(code,title,artist,youtube_id,created) VALUES (?,?,?,?,?)',(code,*row,int(time.time())))
   self.send(201,{'id':cur.lastrowid,'code':code,'title':row[0]});return
  if path=='/api/songs/import':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   songs=d.get('songs',[])
   if not isinstance(songs,list) or len(songs)>2000:self.send(400,{'error':'Provide songs array (maximum 2000)'});return
   count=0
   with db() as c:
    for item in songs:
     if not isinstance(item,dict):continue
     code=str(item.get('code','')).strip()[:120];title=str(item.get('title','')).strip()[:250]
     vid=str(item.get('youtube_id',item.get('youtubeId',''))).strip()
     if not code or not title or (vid and not re.fullmatch(r'[A-Za-z0-9_-]{11}',vid)):continue
     c.execute('INSERT OR REPLACE INTO api_songs(code,title,artist,language,youtube_id) VALUES (?,?,?,?,?)',(code,title,str(item.get('artist',''))[:200],str(item.get('language',''))[:80],vid));count+=1
   self.send(200,{'imported':count});return
  if path=='/api/choose_folder':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   folder=choose_folder()
   if not folder:self.send(200,{'cancelled':True});return
   with db() as c:c.execute("INSERT OR REPLACE INTO settings(k,v) VALUES ('song_folder',?)",(folder,))
   self.send(200,scan_library());return
  if path=='/api/import_songs':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   self.send(200,import_songs());return
  if path=='/api/scan':
   if not self.authorized():self.send(403,{'error':'Host only'});return
   self.send(200,scan_library());return
  self.send(404,{'error':'Not found'})
 def do_DELETE(self):
  path=urllib.parse.urlparse(self.path).path
  if path.startswith('/api/remote/queue/'):
   if not self.authorized():self.send(403,{'error':'Host only'});return
   try:id_=int(path.rsplit('/',1)[1])
   except ValueError:self.send(400,{'error':'Invalid queue ID'});return
   with REMOTE_QUEUE_LOCK:
    with db() as c:c.execute('DELETE FROM remote_queue WHERE id=?',(id_,))
   self.send(200,{'removed':True});return
  if path.startswith('/remote/queue/'):
   if not self.remote_auth():self.send(403,{'error':'Wrong pairing PIN'});return
   try:id_=int(path.rsplit('/',1)[1])
   except ValueError:self.send(400,{'error':'Invalid queue ID'});return
   with REMOTE_QUEUE_LOCK:
    with db() as c:deleted=c.execute('DELETE FROM remote_queue WHERE id=?',(id_,)).rowcount
   self.send(200,{'removed':bool(deleted)});return
  if not self.authorized():self.send(403,{'error':'Host only'});return
  if path.startswith('/api/queue/'):
   try:id_=int(path.rsplit('/',1)[1])
   except ValueError:self.send(400,{'error':'Invalid queue id'});return
   with db() as c:deleted=c.execute('DELETE FROM api_queue WHERE id=?',(id_,)).rowcount
   self.send(200,{'removed':bool(deleted)}) if deleted else self.send(404,{'error':'Queue item not found'});return
  self.send(404,{'error':'Not found'})
def localip():
 try:
  s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80));ip=s.getsockname()[0];s.close();return ip
 except OSError:return '127.0.0.1'
class KaraokeAPI:
 def open_videokeph(self, url='https://videokeph.com/app/'):
  # Keep navigation confined to the official service, not arbitrary user URLs.
  parsed=urllib.parse.urlparse(url)
  if parsed.scheme!='https' or parsed.hostname not in ('videokeph.com','www.videokeph.com'):
   return {'error':'Invalid VideokePH URL'}
  webview.create_window('dannyboi Karaoke | VideokePH Online Player',url,width=1180,height=780,min_size=(800,550))
  return {'opened':True}
def main():
 global PORT
 print("Remote control pairing PIN:",REMOTE_PIN,"Windows IP:",localip(),"Port:",REMOTE_PORT)
 for port in (8765,8766,8767):
  try:
   server=ThreadingHTTPServer(('127.0.0.1',port),Handler);PORT=port;break
  except OSError:continue
 else:raise RuntimeError("Ports 8765-8767 are in use.")
 threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  remote_server=ThreadingHTTPServer(('0.0.0.0',REMOTE_PORT),Handler)
  threading.Thread(target=remote_server.serve_forever,daemon=True).start()
  print(f'dannyboi remote: http://{localip()}:{REMOTE_PORT}  PIN: {REMOTE_PIN}')
 except OSError:
  remote_server=None
  print('Remote port 8877 unavailable; close other apps using it.')
 url=f'http://127.0.0.1:{PORT}/'
 webview.create_window("dannyboi's Karaoke v4.0",url,width=1300,height=800,min_size=(850,600),js_api=KaraokeAPI())
 webview.start(debug=False)
 server.shutdown()
 if remote_server:remote_server.shutdown()
if __name__=='__main__':main()
