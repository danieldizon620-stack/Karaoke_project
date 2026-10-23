let hostToken='', player=null,activeId=null,ready=false;
const $=id=>document.getElementById(id);
const isHost=!!$('ytplayer');
const api=async(path,body)=>{
 const opts=body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-Host-Token':hostToken},body:JSON.stringify(body)};
 const r=await fetch('/api/'+path,opts);const j=await r.json();if(!r.ok)throw Error(j.error||'Request failed');return j;
};
async function init(){
 try{
 const info=await api('info');hostToken=isHost?info.token:'';
 if(isHost)$('remote').textContent='Phone remote: http://'+info.ip+':'+location.port+'/remote (same Wi-Fi)';
 await refresh();
 }catch(e){console.error(e)}
}
async function refresh(){
 try{
 const songs=await api('list'),container=$('queue');container.replaceChildren();
 for(const s of songs){
 const item=document.createElement('div');item.className='song';
 const label=document.createElement('div');label.className='song-title';label.textContent=s.title+(s.singer?' — '+s.singer:'');
 item.appendChild(label);
 if(isHost){
 const b=document.createElement('button');b.textContent='▶';b.title='Play this song';b.onclick=()=>playSong(s);item.appendChild(b);
 const x=document.createElement('button');x.textContent='✕';x.title='Remove';x.onclick=async()=>{await api('done',{id:s.id});if(activeId===s.id)activeId=null;refresh()};item.appendChild(x);
 }
 container.appendChild(item);
 }
 if(!songs.length)container.textContent='Queue is empty. Add a song!';
 return songs;
 }catch(e){$('message').textContent=e.message;return []}
}
function playSong(s){
 if(window.stopLocalPlayback)window.stopLocalPlayback();
 activeId=s.id;$('now').textContent='Now playing: '+s.title+(s.singer?' — '+s.singer:'');
 if(ready&&player){player.loadVideoById(s.video)}else{window.open('https://www.youtube.com/watch?v='+encodeURIComponent(s.video),'_blank')}
}
async function next(){
 const songs=await api('list');
 if(activeId!==null){await api('done',{id:activeId})}
 activeId=null;
 const upcoming=await refresh();
 if(upcoming.length)playSong(upcoming[0]);else if(ready&&player){player.stopVideo();$('now').textContent='Queue finished'}
}
window.onYouTubeIframeAPIReady=()=>{
 if(!isHost)return;
 player=new YT.Player('ytplayer',{width:'100%',height:'100%',videoId:'',playerVars:{playsinline:1,rel:0},events:{onReady:()=>{ready=true},onStateChange:e=>{if(e.data===YT.PlayerState.ENDED)next().catch(console.error)}}});
};
$('add').addEventListener('submit',async e=>{
 e.preventDefault();const d=Object.fromEntries(new FormData(e.target));
 try{await api('add',d);e.target.reset();$('message').textContent='Song added to queue';await refresh()}
 catch(err){$('message').textContent=err.message}
});
if(isHost){
 $('search').onclick=()=>window.open('https://www.youtube.com/results?search_query=karaoke+lyrics','_blank');
 $('play').onclick=async()=>{if(activeId!==null&&ready&&player)player.playVideo();else{const songs=await api('list');if(songs.length)playSong(songs[0])}};
 $('pause').onclick=()=>{if(ready&&player)player.pauseVideo()};
 $('next').onclick=()=>next().catch(console.error);
 $('clear').onclick=async()=>{if(confirm('Clear all queued songs?')){await api('clear',{});activeId=null;if(ready&&player)player.stopVideo();await refresh()}};
 $('full').onclick=()=>{const p=document.querySelector('.player');if(!document.fullscreenElement)p.requestFullscreen?.();else document.exitFullscreen?.()};
}
init();setInterval(refresh,3000);
