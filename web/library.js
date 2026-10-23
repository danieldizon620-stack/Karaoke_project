let librarySongs=[],scanBusy=false,localActive=false;
window.librarySongs=librarySongs;let localQueue=[];
const libEl=id=>document.getElementById(id);
async function loadLibrary(){
 const q=libEl('library-search').value.trim();
 try{const [songs,status]=await Promise.all([fetch('/api/library?q='+encodeURIComponent(q)).then(r=>r.json()),fetch('/api/library_status').then(r=>r.json())]);
 librarySongs=songs;window.librarySongs=songs;libEl('library-status').textContent=(status.folder||'No folder selected')+' • '+status.count+' songs';
 const area=libEl('library-results');area.replaceChildren();
 for(const s of songs){const item=document.createElement('div');item.className='catalog-song';
 const label=document.createElement('span');label.textContent=String(s.id).padStart(5,'0')+' · '+s.title+(s.artist?' — '+s.artist:'')+' ['+s.kind.toUpperCase()+']';item.append(label);
 const b=document.createElement('button');b.textContent='▶ Play';b.onclick=()=>playLocal(s);item.append(b);const q=document.createElement('button');q.textContent='＋ Queue';q.onclick=()=>{localQueue.push(s);renderLocalQueue()};item.append(q);area.append(item)}
 if(!songs.length)area.textContent='No matching songs';
 }catch(e){libEl('library-status').textContent='Library error: '+e.message}
}
async function scan(){if(scanBusy)return;scanBusy=true;libEl('library-status').textContent='Scanning folders…';try{const r=await fetch('/api/scan',{method:'POST',headers:{'X-Host-Token':hostToken,'Content-Type':'application/json'},body:'{}'}).then(r=>r.json());if(r.error)throw Error(r.error);await loadLibrary()}catch(e){libEl('library-status').textContent=e.message}finally{scanBusy=false}}
libEl('choose-folder').onclick=async()=>{libEl('library-status').textContent='Choose a folder on your computer…';try{const r=await fetch('/api/choose_folder',{method:'POST',headers:{'X-Host-Token':hostToken,'Content-Type':'application/json'},body:'{}'}).then(r=>r.json());if(r.error)throw Error(r.error);await loadLibrary()}catch(e){libEl('library-status').textContent=e.message}};
libEl('scan-folder').onclick=scan;
libEl('import-songs').onclick=async()=>{libEl('library-status').textContent='Select song files on this computer…';try{const r=await fetch('/api/import_songs',{method:'POST',headers:{'X-Host-Token':hostToken,'Content-Type':'application/json'},body:'{}'}).then(r=>r.json());if(r.error)throw Error(r.error);await loadLibrary();libEl('library-status').textContent=`Imported ${r.imported||0} files; skipped ${r.skipped||0}. Library: ${r.count||0} songs.`}catch(e){libEl('library-status').textContent=e.message}};
function renderLocalQueue(){const area=libEl('queue');area.replaceChildren();for(const [i,s] of localQueue.entries()){const row=document.createElement('div');row.className='song';row.textContent=`${i+1}. ${s.title} — ${s.artist||'Unknown'}`;const b=document.createElement('button');b.textContent='▶';b.onclick=()=>{localQueue.splice(i,1);renderLocalQueue();playLocal(s)};row.append(b);area.append(row)}if(!localQueue.length)area.textContent='No songs queued';}
window.playNextLocal=()=>{const s=localQueue.shift();renderLocalQueue();if(s)playLocal(s);else libEl('now').textContent='Queue finished'};
window.clearLocalQueue=()=>{localQueue=[];renderLocalQueue()};

let searchDebounce;libEl('library-search').oninput=()=>{clearTimeout(searchDebounce);searchDebounce=setTimeout(loadLibrary,180)};
const localVideo=libEl('local-video'),localAudio=libEl('local-audio'),cdg=libEl('cdg-canvas');
window.stopLocalPlayback=()=>{localVideo.pause();localAudio.pause();localVideo.removeAttribute('src');localAudio.removeAttribute('src');localVideo.load();localAudio.load();libEl('local-player').hidden=true;localActive=false;};
async function playLocal(s){
 if(s.kind==='zip'){libEl('library-status').textContent='Extract ZIP MP3 and CDG files into your Songs folder to play.';return}
 if(window.stopLocalPlayback)window.stopLocalPlayback();
 activeId=null;localActive=true;
 libEl('local-player').hidden=false;
 const media='/api/media/'+s.id;
 localVideo.hidden=s.kind==='mp3';localAudio.hidden=s.kind!=='mp3';cdg.hidden=s.kind!=='mp3';
 const el=s.kind==='mp3'?localAudio:localVideo;el.src=media;el.play().catch(()=>{});
 libEl('now').textContent='Now playing: '+s.title+(s.artist?' — '+s.artist:'');
 el.onended=()=>window.playNextLocal?.();
 if(s.kind==='mp3'){
  try{const response=await fetch(media+'?lyrics=1');if(!response.ok)throw Error('CDG not found');const data=new Uint8Array(await response.arrayBuffer());startCdg(data,el)}catch(e){libEl('library-status').textContent='Lyrics unavailable: '+e.message}
 }
}
let cdgFrame=0;
function startCdg(data,audio){
 const frame=++cdgFrame,ctx=cdg.getContext('2d');const pixels=new Uint8Array(300*216),palette=new Array(16).fill('#000000');let processed=0;
 const render=()=>{
  if(frame!==cdgFrame||!localActive)return;
  const target=Math.min(Math.floor(audio.currentTime*300),Math.floor(data.length/24));
  for(;processed<target;processed++){
   const offset=processed*24;if((data[offset]&63)!==9)continue;
   const cmd=data[offset+1]&63,d=data.subarray(offset+4,offset+20);
   if(cmd===1){pixels.fill(d[0]&15)}
   else if(cmd===30||cmd===31){let base=cmd===30?0:8;for(let i=0;i<8;i++){const x=d[i*2]&63,y=d[i*2+1]&63,z=d[i*2+1]>>6;const r=((x>>2)&15)*17,g=(((x&3)<<2)|((y>>4)&3))*17,b=(y&15)*17;palette[base+i]='rgb('+r+','+g+','+b+')'}}
   else if(cmd===6||cmd===38){let c0=d[0]&15,c1=d[1]&15,row=(d[2]&31)*12,col=(d[3]&63)*6;if(row>204||col>294)continue;
    for(let y=0;y<12;y++)for(let x=0;x<6;x++){const v=(d[4+y]& (1<<(5-x)))?c1:c0;if(cmd===6||v!==0)pixels[(row+y)*300+col+x]=v}
   }
  }
  const im=ctx.createImageData(300,216);for(let i=0;i<pixels.length;i++){const rgb=palette[pixels[i]];const m=rgb.match(/\d+/g);const j=i*4;im.data[j]=+m[0];im.data[j+1]=+m[1];im.data[j+2]=+m[2];im.data[j+3]=255}ctx.putImageData(im,0,0);
  requestAnimationFrame(render);
 };requestAnimationFrame(render)
}
setTimeout(()=>{loadLibrary();scan();renderLocalQueue()},900);
setInterval(()=>{if(!scanBusy)scan()},60000);
