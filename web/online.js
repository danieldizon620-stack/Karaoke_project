// User-curated links only. No scraping, downloading, or embedding third-party content.
(()=>{
 const site='https://videokeph.com/';
 const key='dannyboi_videokeph_links_v1';
 const $=id=>document.getElementById(id);
 let links=[];try{const parsed=JSON.parse(localStorage.getItem(key)||'[]');if(Array.isArray(parsed))links=parsed.filter(x=>x&&x.url&&x.title)}catch{}
 const save=()=>localStorage.setItem(key,JSON.stringify(links));
 const valid=u=>{try{const p=new URL(u);return p.protocol==='https:'&&(p.hostname==='videokeph.com'||p.hostname.endsWith('.videokeph.com'))}catch{return false}};
 const render=()=>{const q=$('online-search').value.trim().toLowerCase(),area=$('online-results');area.replaceChildren();const found=links.filter(x=>(x.title+' '+x.artist).toLowerCase().includes(q));for(const item of found){const row=document.createElement('div');row.className='catalog-song';const label=document.createElement('span');label.textContent=item.title+(item.artist?' — '+item.artist:'');row.append(label);const open=document.createElement('button');open.textContent='↗ Open';open.onclick=()=>window.open(item.url,'_blank','noopener,noreferrer');row.append(open);const remove=document.createElement('button');remove.textContent='Remove';remove.onclick=()=>{links=links.filter(x=>x!==item);save();render()};row.append(remove);area.append(row)}if(!found.length)area.textContent='No saved song links. Add a VideokePH song URL below.';};
 $('videokeph-home').onclick=()=>window.open(site,'_blank','noopener,noreferrer');
 $('online-add').onclick=()=>{const title=$('online-title').value.trim(),artist=$('online-artist').value.trim(),url=$('online-url').value.trim();if(!title||!valid(url)){$('online-message').textContent='Enter a title and a valid https://videokeph.com/ song link.';return}if(links.some(x=>x.url===url)){$('online-message').textContent='This link is already saved.';return}links.push({title,artist,url});save();$('online-title').value='';$('online-artist').value='';$('online-url').value='';$('online-message').textContent='Song link saved on this computer.';render()};
 $('online-search').oninput=render;render();
})();
