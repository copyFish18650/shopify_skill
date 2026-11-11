(() => {
 'use strict';
 const controllers=new Map(),mobile=matchMedia('(max-width:989px)');
 function init(root=document){root.querySelectorAll('[data-catalog-controls]').forEach(owner=>{
  if(controllers.has(owner))return;
  const form=owner.querySelector('[data-catalog-form]'),panel=owner.querySelector('[data-catalog-panel]'),open=owner.querySelector('[data-catalog-open]');
  owner.querySelectorAll('[data-result-number]').forEach(el=>{const count=Number(el.textContent);if(Number.isFinite(count))el.textContent=new Intl.NumberFormat(document.documentElement.lang||'en').format(count);});
  if(!panel||!open){controllers.set(owner,()=>{});return;}
  const canDialog=typeof HTMLDialogElement!=='undefined'&&typeof HTMLDialogElement.prototype.showModal==='function';
  if(!canDialog){controllers.set(owner,()=>{});return;}
  const placeholder=document.createComment('catalog controls desktop position');panel.before(placeholder);const dialog=document.createElement('dialog');dialog.className='catalog-filter-dialog scheme-light';dialog.setAttribute('aria-label',open.textContent.trim());form.append(dialog);owner.classList.add('catalog-enhanced');
  const close=panel.querySelector('[data-catalog-close]');
  const show=()=>{if(mobile.matches&&!dialog.open){dialog.showModal();close.focus();}};
  const hide=()=>dialog.close();const returned=()=>{if(open.getClientRects().length)open.focus();};
  open.addEventListener('click',show);close.addEventListener('click',hide);dialog.addEventListener('close',returned);
  const resize=()=>{if(mobile.matches){dialog.append(panel);}else{const wasOpen=dialog.open;if(wasOpen)dialog.close();placeholder.after(panel);if(wasOpen){const target=panel.querySelector('summary,select');if(target)target.focus();}}};
  mobile.addEventListener('change',resize);resize();
  const rangeValid=()=>{let valid=true;panel.querySelectorAll('[data-price-range]').forEach(range=>{const min=range.querySelector('[data-price-min]'),max=range.querySelector('[data-price-max]'),error=range.querySelector('[data-price-error]');const bad=min.value!==''&&max.value!==''&&Number(min.value)>Number(max.value);max.setCustomValidity(bad?error.textContent:'');error.hidden=!bad;if(bad)valid=false;});return valid;};
  const changed=event=>{rangeValid();const note=panel.querySelector('[data-catalog-draft]');if(note)note.hidden=false;const detail=event.target.closest('[data-catalog-facet]');if(detail){const badge=detail.querySelector('[data-facet-count]');if(badge){const n=detail.querySelectorAll('input[type=checkbox]:checked').length;badge.textContent=String(n);badge.hidden=n===0;}}if(event.target.matches('[data-catalog-sort]')&&!mobile.matches){if(form.requestSubmit)form.requestSubmit();else form.submit();}};
  form.addEventListener('change',changed);form.addEventListener('input',rangeValid);
  const invalid=event=>{const detail=event.target.closest('details');if(detail)detail.open=true;if(mobile.matches&&!dialog.open)show();};form.addEventListener('invalid',invalid,true);
  const applyButton=panel.querySelector('[data-catalog-apply]'),applyText=applyButton?.textContent;
  const restore=()=>{owner.removeAttribute('aria-busy');if(applyButton){applyButton.removeAttribute('aria-busy');applyButton.textContent=applyText;}};window.addEventListener('pageshow',restore);
  const submit=event=>{if(!rangeValid()){event.preventDefault();form.reportValidity();return;}owner.setAttribute('aria-busy','true');if(applyButton){applyButton.setAttribute('aria-busy','true');applyButton.textContent=applyButton.dataset.updatingLabel;}};form.addEventListener('submit',submit);
  const keyboard=event=>{if(event.key!=='Escape'||mobile.matches)return;const detail=event.target.closest('[data-catalog-facet][open]');if(detail){detail.open=false;detail.querySelector('summary').focus();event.preventDefault();}};owner.addEventListener('keydown',keyboard);
  const outside=event=>{if(mobile.matches)return;owner.querySelectorAll('[data-catalog-facet][open]').forEach(detail=>{if(!detail.contains(event.target))detail.open=false;});};document.addEventListener('click',outside);
  controllers.set(owner,()=>{mobile.removeEventListener('change',resize);open.removeEventListener('click',show);close.removeEventListener('click',hide);dialog.removeEventListener('close',returned);form.removeEventListener('change',changed);form.removeEventListener('input',rangeValid);form.removeEventListener('invalid',invalid,true);form.removeEventListener('submit',submit);window.removeEventListener('pageshow',restore);owner.removeEventListener('keydown',keyboard);document.removeEventListener('click',outside);if(dialog.open)dialog.close();placeholder.after(panel);dialog.remove();placeholder.remove();owner.classList.remove('catalog-enhanced');});
 });}
 init();document.addEventListener('shopify:section:load',event=>init(event.target));document.addEventListener('shopify:section:unload',event=>{for(const [owner,cleanup]of controllers){if(event.target.contains(owner)){cleanup();controllers.delete(owner);}}});
})();
