(function(){'use strict';
var pin='', player=null, current=null, queue=[], scoring=false, timer=null;
var $=function(id){return document.getElementById(id)};
function setStatus(s){$('status').textContent=s}
function request(path){return fetch(path,{headers:{'X-Remote-PIN':pin},cache:'no-store'}).then(function(r){if(!r.ok)throw new Error(r.status===403?'Incorrect pairing PIN':'Host unavailable');return r.json()})}
function connect(){var p=$('pin').value.trim();if(!/^\d{6}$/.test(p)){$('error').textContent='Enter the six-digit PIN';return}pin=p;request('/remote/queue').then(function(d){$('overlay').style.display='none';setStatus('Connected to Windows');queue=d.queue||[];tick();timer=setInterval(tick,2000)}).catch(function(e){$('error').textContent=e.message})}
$('connect').addEventListener('click',connect);$('pin').addEventListener('keydown',function(e){if(e.key==='Enter')connect()});
function tick(){request('/remote/queue').then(function(d){queue=d.queue||[];$('next').textContent='Queue: '+queue.length;if(!current&&!scoring&&queue.length)start(queue[0]);setStatus('Connected to Windows')}).catch(function(){setStatus('Connection lost — check Windows host');clearInterval(timer);timer=null;$('overlay').style.display='flex';$('error').textContent='Re-enter PIN to reconnect'})}
function start(item){if(!item||!item.videoId||!/^[\w-]{11}$/.test(item.videoId))return;current=item;$('now').textContent='Now playing: '+item.title;if(player&&player.loadVideoById){player.loadVideoById(item.videoId)}else if(window.YT&&YT.Player){player=new YT.Player('player',{width:'100%',height:'100%',videoId:item.videoId,playerVars:{autoplay:1,playsinline:1,rel:0},events:{onStateChange:onState,onError:onError}})}else{setStatus('Waiting for YouTube player...')}}
function removeCurrent(){if(!current)return Promise.resolve();var id=current.id;return fetch('/remote/queue/'+encodeURIComponent(id),{method:'DELETE',headers:{'X-Remote-PIN':pin}}).catch(function(){})}
function end(){if(scoring||!current)return;scoring=true;$('score').style.display='flex';removeCurrent().then(function(){current=null;setTimeout(function(){$('score').style.display='none';scoring=false;tick()},4500)})}
function onState(e){if(e.data===0)end()}
function onError(){setStatus('Video unavailable on TV; skipping');if(current){removeCurrent().then(function(){current=null;setTimeout(tick,1500)})}}
window.onYouTubeIframeAPIReady=function(){if(current&&!player)start(current)};
window.addEventListener('keydown',function(e){if(e.key==='Escape'&&current){end()} });
})();
