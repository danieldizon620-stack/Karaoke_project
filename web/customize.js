(() => {
 const choice=document.getElementById('background-choice'),upload=document.getElementById('background-upload'),reset=document.getElementById('background-reset');
 const search=document.getElementById('catalog-search'),list=document.getElementById('catalog');
 if(!choice)return;
 const key='dannybois-karaoke-bg-v22',photoKey='dannybois-karaoke-bg-photo-v22';
 function apply(mode){
  document.body.dataset.background=mode;
  document.body.style.backgroundImage='';
  if(mode==='custom'){
   try{const url=localStorage.getItem(photoKey);if(url)document.body.style.backgroundImage='linear-gradient(#1b001aa6,#1b001a9e),url('+JSON.stringify(url)+')';}catch(e){}
  }
  choice.value=mode;
 }
 let saved='purple';try{saved=localStorage.getItem(key)||'purple';}catch(e){}
 apply(saved);
 choice.onchange=()=>{try{localStorage.setItem(key,choice.value)}catch(e){}apply(choice.value)};
 upload.onchange=()=>{
  const file=upload.files&&upload.files[0];if(!file)return;
  if(!['image/png','image/jpeg','image/webp'].includes(file.type)){alert('Use PNG, JPG or WebP.');return;}
  if(file.size>2*1024*1024){alert('Please select a photo under 2 MB.');return;}
  const reader=new FileReader();
  reader.onload=()=>{try{localStorage.setItem(photoKey,reader.result);localStorage.setItem(key,'custom');apply('custom')}catch(e){alert('This photo is too large for browser storage. Try a smaller image.')}};
  reader.readAsDataURL(file);
 };
 reset.onclick=()=>{try{localStorage.removeItem(key);localStorage.removeItem(photoKey)}catch(e){}apply('purple');upload.value=''};
 let songs=[];
 function render(){
  list.replaceChildren();
  const q=search.value.trim().toLowerCase();
  const filtered=songs.filter(s=>(s.title+' '+s.artist).toLowerCase().includes(q)).slice(0,40);
  for(const song of filtered){
   const row=document.createElement('div');row.className='catalog-song';
   const name=document.createElement('span');name.textContent=song.title+' — '+song.artist;
   const button=document.createElement('button');button.type='button';button.textContent='Find karaoke';
   button.onclick=()=>{
    const title=document.querySelector('#add input[name=title]');
    if(title)title.value=song.title+' - '+song.artist;
    window.open('https://www.youtube.com/results?search_query='+encodeURIComponent(song.title+' '+song.artist+' karaoke lyrics'),'_blank','noopener');
   };
   row.append(name,button);list.append(row);
  }
  if(!filtered.length)list.textContent='No matches. You can still add any song using its YouTube link.';
 }
 fetch('/starter_songs.json').then(r=>r.json()).then(data=>{songs=data;render()}).catch(()=>{list.textContent='Catalog unavailable; manual song entry still works.'});
 search.oninput=render;
})();