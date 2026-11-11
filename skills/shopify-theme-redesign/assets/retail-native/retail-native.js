/* Small native enhancements. No catalog fetch, trackers or checkout overrides. */
(() => {
 'use strict';
 const body=document.body, motion=()=>body.classList.contains('retail-motion')&&!matchMedia('(prefers-reduced-motion: reduce)').matches;
 const imageDialog=document.querySelector('[data-retail-image-dialog]');let imageTrigger=null;
 if(imageDialog&&typeof imageDialog.showModal==='function'){
   const media=imageDialog.querySelector('[data-retail-image-content]'),error=imageDialog.querySelector('[data-retail-image-error]');
   imageDialog.querySelector('[data-retail-image-close]').addEventListener('click',()=>imageDialog.close());
   imageDialog.addEventListener('close',()=>{media.replaceChildren();if(imageTrigger&&imageTrigger.isConnected)imageTrigger.focus();});
   imageDialog.addEventListener('click',event=>{if(event.target!==imageDialog)return;const r=imageDialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)imageDialog.close();});
   document.addEventListener('click',event=>{
     const link=event.target.closest('[data-retail-image-open]');if(!link||event.defaultPrevented||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
     event.preventDefault();imageTrigger=link;const img=new Image();img.alt=link.dataset.imageAlt||'';img.src=link.href;error.hidden=true;
     img.addEventListener('error',()=>{if(media.contains(img)){media.replaceChildren();error.hidden=false;}},{once:true});
     imageDialog.querySelector('[data-retail-image-label]').textContent=link.dataset.imageAlt||'';media.replaceChildren(img);imageDialog.showModal();imageDialog.querySelector('button').focus();
   });
 }
 document.addEventListener('keydown',event=>{
   if(event.key!=='Escape')return;
   const open=[...document.querySelectorAll('.catalog-header .nav-dropdown[open],.catalog-header .header-search[open],.catalog-header .mobile-menu[open]')];
   const closest=event.target.closest('details');const owner=open.includes(closest)?closest:open[open.length-1];
   if(owner){open.forEach(el=>el.open=false);owner.querySelector('summary').focus();event.preventDefault();}
 },true);
 document.addEventListener('click',event=>document.querySelectorAll('.catalog-header .nav-dropdown[open],.catalog-header .header-search[open]').forEach(detail=>{if(!detail.contains(event.target))detail.open=false;}));
 document.addEventListener('toggle',event=>{
   if(event.target.matches('.catalog-header .header-search')&&event.target.open){const input=event.target.querySelector('input[type=search]');if(input)input.focus();}
 },true);
 const initialized=new Map();
 function init(root=document){
   root.querySelectorAll('.catalog-header .nav-dropdown').forEach(detail=>{
     if(initialized.has(detail))return;let timer;
     const enter=event=>{if(event.pointerType!=='mouse'||!matchMedia('(hover:hover) and (pointer:fine)').matches)return;clearTimeout(timer);timer=setTimeout(()=>detail.open=true,100);};
     const leave=()=>{clearTimeout(timer);timer=setTimeout(()=>{if(!detail.contains(document.activeElement))detail.open=false;},160);};
     detail.addEventListener('pointerenter',enter);detail.addEventListener('pointerleave',leave);
     initialized.set(detail,()=>{clearTimeout(timer);detail.removeEventListener('pointerenter',enter);detail.removeEventListener('pointerleave',leave);});
   });
   root.querySelectorAll('.product-form .quantity-input').forEach(input=>{
     if(body.dataset.quantityButtons!=='true'||input.closest('.retail-stepper'))return;
     const group=document.createElement('div');group.className='retail-stepper';const minus=document.createElement('button'),plus=document.createElement('button');
     minus.type=plus.type='button';minus.textContent='−';plus.textContent='+';minus.setAttribute('aria-label',body.dataset.quantityDecrease);plus.setAttribute('aria-label',body.dataset.quantityIncrease);
     input.replaceWith(group);group.append(minus,input,plus);
     function state(){const value=Number(input.value),min=input.min===''?1:Number(input.min);minus.disabled=input.disabled||value<=min;plus.disabled=input.disabled||(input.max!==''&&value>=Number(input.max));}
     const change=direction=>{if(!input.checkValidity())input.value=input.min||'1';direction<0?input.stepDown():input.stepUp();input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));state();};
     minus.addEventListener('click',()=>change(-1));plus.addEventListener('click',()=>change(1));input.addEventListener('input',state);input.addEventListener('change',state);
     const observer=new MutationObserver(state);observer.observe(input,{attributes:true,attributeFilter:['min','max','step','disabled']});initialized.set(group,()=>observer.disconnect());state();
   });
   root.querySelectorAll('[data-product-price]').forEach(price=>{
     if(initialized.has(price))return;let timer;const observer=new MutationObserver(()=>{if(!motion())return;price.classList.remove('retail-price-updated');requestAnimationFrame(()=>price.classList.add('retail-price-updated'));clearTimeout(timer);timer=setTimeout(()=>price.classList.remove('retail-price-updated'),300);});observer.observe(price,{childList:true});initialized.set(price,()=>{observer.disconnect();clearTimeout(timer);});
   });
   root.querySelectorAll('[data-cart-count]').forEach(count=>{
     if(initialized.has(count))return;let timer;const observer=new MutationObserver(()=>{if(!motion())return;count.classList.remove('retail-count-updated');requestAnimationFrame(()=>count.classList.add('retail-count-updated'));clearTimeout(timer);timer=setTimeout(()=>count.classList.remove('retail-count-updated'),300);});observer.observe(count,{childList:true,characterData:true,subtree:true});initialized.set(count,()=>{observer.disconnect();clearTimeout(timer);});
   });
 }
 const quickContent=document.querySelector('[data-quick-look-content]');if(quickContent){const observer=new MutationObserver(()=>{for(const [element,cleanup] of initialized){if(!element.isConnected){cleanup();initialized.delete(element);}}init(quickContent);});observer.observe(quickContent,{childList:true});}
 init();document.addEventListener('shopify:section:load',event=>init(event.target));
 document.addEventListener('shopify:section:unload',event=>{for(const [element,cleanup] of initialized){if(event.target.contains(element)){cleanup();initialized.delete(element);}}});
})();
