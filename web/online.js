// VideokePH runs in its own window, using the provider's official search and player.
(()=>{
 const $=id=>document.getElementById(id);
 const key='dannyboi_videokeph_links_v1';
 let links=[];try{let v=JSON.parse(localStorage.getItem(key)||'[]');if(Array.isArray(v))links=v.filter(x=>x&&x.url&&x.title)}catch{}
 const save=()=>localStorage.setItem(key,JSON.stringify(links));
 const valid=u=>{try{let p=new URL(u);return p.protocol==='https:'&&(p.hostname==='videokeph.com'||p.hostname.endsWith('.videokeph.com'))}catch{return false}};
 function openSite(url='https://videokeph.com/app/'){
   if(window.pywebview?.api?.open_videokeph){window.pywebview.api.open_videokeph(url).catch(()=>window.open(url,'_blank','noopener,noreferrer'))}
   else window.open(url,'_blank','noopener,noreferrer');
 }
 function render(){const q=$('online-search').value.trim().toLowerCase(),area=$('online-results');area.replaceChildren();let found=links.filter(x=>(x.title+' '+(x.artist||'')).toLowerCase().includes(q));for(let item of found){let row=document.createElement('div');row.className='catalog-song';let label=document.createElement('span');label.textContent=item.title+(item.artist?' — '+item.artist:'');row.append(label);let open=document.createElement('button');open.textContent='▶ Open in VideokePH';open.onclick=()=>openSite(item.url);row.append(open);let remove=document.createElement('button');remove.textContent='Remove';remove.onclick=()=>{links=links.filter(x=>x!==item);save();render()};row.append(remove);area.append(row)}if(!found.length)area.textContent='No saved links. Use Live Search to find songs directly on VideokePH.'}
 $('videokeph-home').onclick=()=>openSite();
 $('videokeph-live-search').onclick=()=>openSite();
 $('online-add').onclick=()=>{let title=$('online-title').value.trim(),artist=$('online-artist').value.trim(),url=$('online-url').value.trim();if(!title||!valid(url)){$('online-message').textContent='Enter a title and a valid VideokePH URL.';return}if(links.some(x=>x.url===url)){$('online-message').textContent='This link is already saved.';return}links.push({title,artist,url});save();for(let id of ['online-title','online-artist','online-url'])$(id).value='';$('online-message').textContent='Song link saved.';render()};
 $('online-search').oninput=render;render();
})();
