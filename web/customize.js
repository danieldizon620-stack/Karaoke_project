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

})();
