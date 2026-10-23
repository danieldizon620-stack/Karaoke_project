let hostToken='',activeId=null;
const $=id=>document.getElementById(id);
async function api(path,opts={}){await ready;const r=await fetch('/api/'+path,{...opts,headers:{'X-Host-Token':hostToken,...(opts.headers||{})}});const j=await r.json();if(!r.ok)throw Error(j.error||'Request failed');return j}
async function init(){const info=await fetch('/api/info').then(r=>r.json());hostToken=info.token||'';}
const ready=init();
window.addEventListener('DOMContentLoaded',()=>{$('play').onclick=()=>{if(localActive){const el=$('local-audio').hidden?$('local-video'):$('local-audio');el.play()}else if(window.librarySongs?.length)playLocal(window.librarySongs[0])};$('pause').onclick=()=>{$('local-video').pause();$('local-audio').pause()};$('next').onclick=()=>window.playNextLocal?.();$('clear').onclick=()=>window.clearLocalQueue?.();});
