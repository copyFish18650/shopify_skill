#!/usr/bin/env python3
"""Add native service Pages, deduplicated Footer links and localization to new skill bases.

Local files only. This adapter targets the skill's native base after policy seeding;
it neither creates Shopify Page records nor changes backend markets or prices.
Use --refresh-manifest-only after category/body/address edits and before packaging.
"""
import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path

ASSETS=Path(__file__).resolve().parents[1]/'assets/native-service-pages'
SCHEMA=re.compile(r'({%-?\s*schema\s*-?%})(.*?)({%-?\s*endschema\s*-?%})',re.S)
FOOTER_PREFACE=(ASSETS/'footer-preface.liquid').read_text(encoding='utf-8')
MENUS=(ASSETS/'footer-menus.liquid').read_text(encoding='utf-8')
KINDS={
 'about':('about-us',['about'],None),
 'payment':('payment-terms',['payment'],None),
 'size':('product-guide',['pet-tools-care','tools-product-guide','size-guide','tools-care','product-guides','size-care-guide'],None),
 'tracking':('order-tracking',['track-order','tracking'],None),
 'contact':('contact',['contact-us'],None),
 'privacy_choices':('privacy-choices',['your-privacy-choices','data-sale-opt-out'],None),
 'privacy':('privacy-policy',[],'PRIVACY_POLICY'),
 'returns':('refund-policy',['return-refund-policy','return-and-refund-policy','returns'],'REFUND_POLICY'),
 'shipping':('shipping-policy',[],'SHIPPING_POLICY'),
 'after_sales':('after-sales-support',['after-sales','customer-support'],None),
 'terms':('terms-of-service',[],'TERMS_OF_SERVICE'),
 'contact_information':('contact-information',[],'CONTACT_INFORMATION'),
 'legal':('legal-notice',[],'LEGAL_NOTICE'),
 'sale_terms':('terms-of-sale',[],'TERMS_OF_SALE'),
}
def need(value,message):
    if not value:raise ValueError(message)
require=need
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write_json(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(data):return hashlib.sha256(data).hexdigest()

def schema_suffix(text):
    match = re.search(r'{%-?\s*schema\s*-?%}', text)
    require(match is not None, 'Missing Footer schema')
    return text[match.start():]

def shortcut(kind, setting, label, override=''):
    return ('{% if section.settings.'+setting+' %}\n'
        '{% assign shortcut_document = nil %}{% for information_block in section.blocks %}{% if information_block.type == \'information\' and information_block.settings.kind == \''+kind+'\' %}{% assign shortcut_document = information_block %}{% break %}{% endif %}{% endfor %}\n'
        '{% capture shortcut_url %}{% render \'footer-document-url\', document:shortcut_document'+override+' %}{% endcapture %}{% assign shortcut_url = shortcut_url | strip %}\n'
        '<div class="footer-contact footer-page-shortcut">{% if shortcut_url != blank %}<a href="{{ shortcut_url | escape }}">{{ \''+label+'\' | t }}</a>{% else %}<span class="footer-document-pending" aria-disabled="true">{{ \''+label+'\' | t }}</span>{% endif %}</div>\n'
        '{% endif %}\n')

def patch_footer(source):
    suffix = schema_suffix(source)
    source = source[:-len(suffix)].replace('block.settings.body != blank','block.settings.title != blank')+suffix
    contact_start = source.index('{% if section.settings.show_contact %}')
    guide_start = source.index('{% if section.settings.show_size_help %}', contact_start)
    newsletter_start = source.index('{% if section.settings.newsletter_enable %}', guide_start)
    source = source[:contact_start]+shortcut('contact','show_contact','footer.contact')+shortcut('size','show_size_help','footer.size',', override_page:section.settings.size_guide')+source[newsletter_start:]
    start = source.index('{% assign published_policy = nil %}')
    end = source.index('{% endif %}{% endfor %}',start)
    replacement = '''{% capture document_url %}{% render 'footer-document-url', document:block %}{% endcapture %}{% assign document_url = document_url | strip %}
<li {{ block.shopify_attributes }}>{% if document_url != blank %}<a data-policy-kind="{{ block.settings.kind }}" href="{{ document_url | escape }}">{{ block.settings.title | escape }}</a>{% else %}{% assign pending_document_count = pending_document_count | plus:1 %}<span class="footer-document-pending" data-policy-kind="{{ block.settings.kind }}" aria-disabled="true">{{ block.settings.title | escape }}</span>{% endif %}</li>
'''
    source = source[:start]+replacement+source[end:]
    marker = '{% if section.settings.show_information %}'
    first = source.index(marker)
    source = source[:first]+'{% assign pending_document_count = 0 %}\n'+source[first:]
    dialog = source.index('<dialog class="information-dialog')
    begin = source.rfind('{% if section.settings.show_information %}',0,dialog)
    close = source.index('</footer>',dialog)
    notice = '''{% if request.design_mode and section.settings.show_information and pending_document_count > 0 %}
<p data-service-pages-setup role="status">Publish the corresponding Shopify Pages to activate {{ pending_document_count }} footer document links. Page templates do not create Pages. Existing published Page overrides and store policies remain available.</p>
{% endif %}
'''
    source = source[:begin]+notice+source[close:]
    require(schema_suffix(source) == suffix, 'Footer schema/default/preset bytes changed')
    require('data-info-open' not in source and '<dialog class="information-dialog' not in source, 'A document modal remains')
    return source

def once(text,old,new,label):
    need(text.count(old)==1,'Expected one '+label+' anchor, found '+str(text.count(old)))
    return text.replace(old,new,1)

def replace_schema(text,fn):
    match=SCHEMA.search(text);need(match,'Missing section schema')
    original=json.loads(match.group(2));new=fn(json.loads(match.group(2)))
    line='\r\n' if '\r\n' in match.group(2) else '\n'
    value=json.dumps(new,ensure_ascii=False,indent=2).replace('\n',line)
    return text[:match.start(2)]+line+value+line+text[match.end(2):],original,new

def footer(source):
    schema=SCHEMA.search(source);need(schema,'Footer schema absent');prefix=source[:schema.start()]
    prefix=once(prefix,'<div class="footer-top">',FOOTER_PREFACE+'<div class="footer-top">','footer preface')
    prefix=once(prefix,'{% if section.settings.show_contact %}','{% if section.settings.show_contact and footer_contact_document_present == false %}','contact duplicate guard')
    prefix=once(prefix,'{% if section.settings.show_size_help %}','{% if section.settings.show_size_help and footer_guide_document_present == false %}','guide duplicate guard')
    # Shortcuts may precede or follow menus in different original art directions.
    # Only their actual target is registered; a later duplicate leaves no empty wrapper.
    for key in ('contact','size'):
        shortcut='<div class="footer-contact footer-page-shortcut">{% if shortcut_url != blank %}<a href="{{ shortcut_url | escape }}">{{ \'footer.'+key+'\' | t }}</a>{% else %}<span class="footer-document-pending" aria-disabled="true">{{ \'footer.'+key+'\' | t }}</span>{% endif %}</div>'
        replacement='{% capture footer_url_key %}|{{ shortcut_url }}|{% endcapture %}{% assign shortcut_is_duplicate = false %}{% if shortcut_url != blank and footer_seen_urls contains footer_url_key %}{% assign shortcut_is_duplicate = true %}{% endif %}{% unless shortcut_is_duplicate %}'+shortcut.replace('<a href=', '{% assign footer_seen_urls = footer_seen_urls | append: footer_url_key %}<a href=',1)+'{% endunless %}'
        prefix=once(prefix,shortcut,replacement,'left '+key+' shortcut ledger')
    start=prefix.index('<div class="footer-menus">')
    final_loop=prefix.index("{% for block in section.blocks %}{% case block.type %}",start)
    end_loop=prefix.index('{% endfor %}',final_loop)+len('{% endfor %}')
    closing=re.match(r'\s*</div>',prefix[end_loop:]);need(closing,'Footer menu closing tag changed')
    end=end_loop+closing.end()
    # Replace only footer-menus itself. Some originals place support/address/newsletter
    # after the menus; all of that surrounding original structure is retained verbatim.
    prefix=prefix[:start]+MENUS.rstrip()+prefix[end:]
    prefix=once(prefix,"{% render 'localization', location:'footer' %}","{% render 'localization', location:'footer', section_id:section.id, show_language:section.settings.show_language_selector, show_country:section.settings.show_country_selector %}",'footer localization call')
    result=prefix+source[schema.start():]
    def add_flags(value):
        settings=value['settings'];ids={s.get('id') for s in settings};need(not ids & {'show_language_selector','show_country_selector'},'Localization flags already exist')
        settings.extend([{'type':'checkbox','id':'show_language_selector','label':'Show language selector','default':True},{'type':'checkbox','id':'show_country_selector','label':'Show country and currency','default':True}]);return value
    result,before,after=replace_schema(result,add_flags)
    need(after['settings'][:-2]==before['settings'] and after.get('blocks')==before.get('blocks') and after.get('presets')==before.get('presets'),'Footer old settings changed')
    return result

def announcement(source,copy):
    source=once(source,'<div class="announcement scheme-{{ section.settings.color_scheme }}">','<div class="announcement scheme-{{ section.settings.color_scheme }}" data-sale-announcement>','announcement wrapper')
    def update(value):
        found=0
        for setting in value['settings']:
            if setting.get('id')=='text':setting['default']=copy;found+=1
        need(found==1,'Expected one announcement text setting')
        for preset in value.get('presets',[]):preset.setdefault('settings',{})['text']=copy
        return value
    return replace_schema(source,update)[0]

def refresh_service_manifest(theme, source_id=None, source_archive=None, source_sha256=None):
    """Refresh local editable Page drafts; it does not overwrite published Page records."""
    theme=Path(theme).resolve();manifest_path=theme/'assets/service-pages-manifest.json'
    previous=read(manifest_path) if manifest_path.exists() else {}
    source_id=(source_id or previous.get('source_id') or theme.name).strip()
    archive_name=source_archive or previous.get('source_zip',{}).get('path')
    archive_sha=source_sha256 or previous.get('source_zip_sha256')
    need(source_id and archive_name and re.fullmatch(r'[a-f0-9]{64}',archive_sha or ''),'Manifest requires genuine source archive provenance')
    group_bytes=(theme/'sections/footer-group.json').read_bytes();group=json.loads(group_bytes.decode('utf-8-sig'))
    footers=[(key,value) for key,value in group.get('sections',{}).items() if value.get('type')=='footer']
    need(len(footers)==1,'Expected one native Footer record')
    section_id,record=footers[0];address=record.get('settings',{}).get('operator_address','');documents=[]
    blocks=record.get('blocks',{});order=record.get('block_order',list(blocks))
    need(len(order)==len(set(order)) and all(key in blocks for key in order),'Footer block order contains missing or duplicate blocks')
    for block_id in order:
        block=blocks[block_id]
        if block.get('type')!='information':continue
        settings=block.get('settings',{});kind=settings.get('kind');need(kind in KINDS,'Unknown document kind: '+str(kind))
        handle,aliases,policy_type=KINDS[kind];body=settings.get('body','');body_html=body
        if not settings.get('title','').strip() or not body.strip():continue
        if kind in {'contact_information','legal'} and address:
            body_html+='<div class="information-address"><h3>Contact address</h3><address>'+html.escape(address,quote=True).replace('\n','<br>')+'</address></div>'
        documents.append({'kind':kind,'title':settings.get('title',''),'suggested_handle':handle,'aliases':aliases,'body_html':body_html,'source_body_html':body,'source_body_sha256':digest(body.encode('utf-8')),'current_override':settings.get('page'),'prefer_store':bool(settings.get('prefer_store',False)),'template_suffix':'contact' if kind=='contact' else 'service','native_policy_type':policy_type,'source_block_id':block_id})
    need(documents and len({d['kind'] for d in documents})==len(documents),'Footer Page drafts must have nonempty content and unique known document kinds')
    value={'schema_version':1,'source_id':source_id,'source_zip':{'path':archive_name,'sha256':archive_sha},'source_zip_sha256':archive_sha,'source_footer_group_sha256':digest(group_bytes),'source_footer':{'section_id':section_id,'operator_address':address,'document_count':len(documents)},'documents':documents,'backend_pages_created':False,'editing_contract':'Published Page bodies are maintained in Shopify Pages. Footer draft blocks and local ZIP files do not synchronize back from Pages. Native policies are read only.','installation_note':'Page templates and this content manifest do not create Shopify Pages. Publish actual Page resources to activate missing links.','provenance_note':'source_zip identifies the genuine source archive, not the generated final ZIP; final archive hashes belong in the external delivery record.'}
    write_json(manifest_path,value)
    return {'manifest':str(manifest_path),'documents':len(documents),'source_id':source_id,'source_footer_group_sha256':value['source_footer_group_sha256'],'backend_pages_created':False}

def update_promotion(theme, announcement_text='Explore the collection', promotion_ready=False):
    """Enable a campaign only after the task's product prices have been verified."""
    theme=Path(theme).resolve();announcement_text=' '.join(announcement_text.split())
    need(bool(announcement_text),'Announcement text must not be empty')
    rates=re.findall(r'(?i)(\d+(?:\.\d+)?)\s*%\s*(?:off|discount|less)',announcement_text)
    need(not promotion_ready or len(set(rates))==1,'An enabled promotion needs one explicit verified discount percentage in --announcement-text')
    need(not promotion_ready or 0<float(rates[0])<100,'Promotion percentage must be between zero and 100')
    announce_path=theme/'sections/announcement-bar.liquid';announce=announce_path.read_text(encoding='utf-8')
    if 'data-sale-announcement' in announce:announce=announce.replace(' data-sale-announcement','',1)
    announce_path.write_text(announcement(announce,announcement_text),encoding='utf-8')
    group_path=theme/'sections/header-group.json';header=read(group_path);count=0
    for record in header.get('sections',{}).values():
        if record.get('type')=='announcement-bar':
            record.setdefault('settings',{})['text']=announcement_text
            record['disabled']=not promotion_ready;count+=1
    need(count==1,'Expected one saved native announcement');write_json(group_path,header)
    for locale_path in (theme/'locales').glob('*.json'):
        if '.schema.' in locale_path.name:continue
        locale=read(locale_path)
        if isinstance(locale.get('wc'),dict) and 'reference_price_note' in locale['wc']:
            locale['wc']['reference_price_note']=(f'Save {rates[0]}% compared with the listed reference retail price.' if promotion_ready else 'Compared with the listed reference retail price.')
            write_json(locale_path,locale)
    return {'announcement':announcement_text,'promotion_ready':bool(promotion_ready),'announcement_enabled':bool(promotion_ready),'prices_changed':False}

def apply_native_service_pages(theme, announcement_text='Explore the collection', source_id=None, source_archive=None, source_sha256=None, promotion_ready=False):
    """Apply functional defaults once, preserving seeded document/schema/native data."""
    theme=Path(theme).resolve();footer_path=theme/'sections/footer.liquid';source=footer_path.read_text(encoding='utf-8')
    need('data-catalog-header' in (theme/'sections/header.liquid').read_text(encoding='utf-8'),'Apply only to this skill native base after retail preparation')
    before_group=(theme/'sections/footer-group.json').read_bytes()
    config_before={name:(theme/name).read_bytes() for name in ['config/settings_data.json','config/settings_schema.json']}
    contact_before=(theme/'sections/contact.liquid').read_bytes()
    first_application='data-info-open' in source or '<dialog class="information-dialog' in source
    if first_application:
        source=footer(patch_footer(source));footer_path.write_text(source,encoding='utf-8')
    else:
        need('footer_seen_urls' in source and "render 'footer-document-url'" in source,'Unrecognized Footer; do not replace a merchant theme')
    for asset,destination in [('footer-document-url.liquid','snippets/footer-document-url.liquid'),('main-service-page.liquid','sections/main-service-page.liquid'),('page.service.json','templates/page.service.json'),('service-pages.css','assets/service-pages.css'),('localization.liquid','snippets/localization.liquid'),('store-controls.css','assets/store-controls.css')]:
        if first_application or not (theme/destination).exists():shutil.copyfile(ASSETS/asset,theme/destination)
    layout_path=theme/'layout/theme.liquid';layout=layout_path.read_text(encoding='utf-8')
    additions=[]
    if "'service-pages.css' | asset_url" not in layout:additions.append("{% if request.page_type == 'page' and template.suffix == 'service' %}{{ 'service-pages.css' | asset_url | stylesheet_tag }}{% endif %}")
    if "'store-controls.css' | asset_url" not in layout:additions.append("{{ 'store-controls.css' | asset_url | stylesheet_tag }}")
    if additions:
        need(layout.count('</head>')==1,'Expected one closing head')
        layout_path.write_text(layout.replace('</head>','\n'.join(additions)+'\n</head>',1),encoding='utf-8')
    promotion_result=update_promotion(theme,announcement_text,promotion_ready)
    need((theme/'sections/footer-group.json').read_bytes()==before_group,'Saved Footer document/settings changed unexpectedly')
    need(all((theme/name).read_bytes()==value for name,value in config_before.items()),'Global merchant settings changed unexpectedly')
    need((theme/'sections/contact.liquid').read_bytes()==contact_before,'Native contact page/form changed unexpectedly')
    result=refresh_service_manifest(theme,source_id,source_archive,source_sha256)
    result.update({'native_localization':True,'duplicate_links_removed':True,'price_multiplier_source':'Explicit per-site promotion plan; no fixed default','backend_settings_changed':False});result.update(promotion_result)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('theme_dir',type=Path)
    parser.add_argument('--refresh-manifest-only',action='store_true',help='After final Footer category/body/address edits, refresh drafts without replacing presentation assets')
    parser.add_argument('--announcement-text',default='Explore the collection',help='Explicit verified per-site campaign copy; no default percentage')
    parser.add_argument('--promotion-ready',action='store_true',help='Enable saved sale banner only after actual current catalog repricing was verified; does not change prices')
    parser.add_argument('--source-id');parser.add_argument('--source-archive');parser.add_argument('--source-sha256');args=parser.parse_args()
    if args.refresh_manifest_only:
        result=refresh_service_manifest(args.theme_dir,args.source_id,args.source_archive,args.source_sha256)
        if args.promotion_ready:result.update(update_promotion(args.theme_dir,args.announcement_text,True))
    else:result=apply_native_service_pages(args.theme_dir,args.announcement_text,args.source_id,args.source_archive,args.source_sha256,args.promotion_ready)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
