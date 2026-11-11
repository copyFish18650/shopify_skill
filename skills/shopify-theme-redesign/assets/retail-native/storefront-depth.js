(()=>{'use strict';
const init=root=>{
 root.querySelectorAll('[data-product-section]').forEach(info=>{
  if(info.dataset.depthReady)return;info.dataset.depthReady='true';
  const select=info.querySelector('[data-variant-select]');
  if(select&&select.options.length>1&&select.options.length<=12&&info.dataset.variantButtons==='true'){
   const group=document.createElement('div');group.className='variant-choices';group.setAttribute('role','group');group.setAttribute('aria-labelledby',select.labels[0]?.id||'');
   select.labels[0]?.setAttribute('id','VariantLabel-'+select.id);group.setAttribute('aria-labelledby','VariantLabel-'+select.id);
   const buttons=[...select.options].map(option=>{const b=document.createElement('button');b.type='button';b.textContent=option.textContent;b.dataset.variantValue=option.value;b.setAttribute('aria-pressed',String(option.selected));b.addEventListener('click',()=>{select.value=option.value;select.dispatchEvent(new Event('change',{bubbles:true}));});group.append(b);return b;});
   select.after(group);select.classList.add('variant-select-fallback');select.tabIndex=-1;select.setAttribute('aria-hidden','true');
   const sync=()=>buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.variantValue===select.value)));select.addEventListener('change',sync);
  }
 });
 root.querySelectorAll('[data-product-gallery="focus"]').forEach(gallery=>{
  if(gallery.dataset.galleryReady)return;gallery.dataset.galleryReady='true';const media=[...gallery.querySelectorAll('.product-media')];
  if(media.length<2||media.some(m=>m.dataset.mediaType!=='image'))return;
  const nav=document.createElement('div');nav.className='product-thumbnails';nav.setAttribute('role','group');nav.setAttribute('aria-label',gallery.dataset.galleryLabel);let current=0;
  const show=(n,focus)=>{current=n;media.forEach((m,i)=>m.hidden=i!==n);[...nav.children].forEach((b,i)=>b.setAttribute('aria-pressed',String(i===n)));if(focus)nav.children[n].focus();};
  media.forEach((m,i)=>{const img=m.querySelector('img');const b=document.createElement('button');b.type='button';b.setAttribute('aria-label',gallery.dataset.photoLabel+' '+(i+1));const thumb=document.createElement('img');try{const u=new URL(img.currentSrc||img.src,location.href);u.searchParams.set('width','160');thumb.src=u.href;}catch{thumb.src=img.src;}thumb.alt='';thumb.width=72;thumb.height=72;thumb.loading='lazy';b.append(thumb);b.addEventListener('click',()=>show(i));b.addEventListener('keydown',e=>{let next=current;if(e.key==='ArrowRight'||e.key==='ArrowDown')next=(current+1)%media.length;else if(e.key==='ArrowLeft'||e.key==='ArrowUp')next=(current+media.length-1)%media.length;else if(e.key==='Home')next=0;else if(e.key==='End')next=media.length-1;else return;e.preventDefault();show(next,true);});nav.append(b);});
  gallery.prepend(nav);gallery.classList.add('gallery-enhanced');show(0);
 });
 root.querySelectorAll('[data-store-policy]').forEach(link=>{if(link.dataset.ready)return;link.dataset.ready='true';link.addEventListener('click',e=>{const target=document.querySelector('.site-footer [data-policy-kind="'+link.dataset.storePolicy+'"]');if(target){e.preventDefault();target.click();}});});
};
init(document);document.addEventListener('shopify:section:load',e=>init(e.target));
})();
