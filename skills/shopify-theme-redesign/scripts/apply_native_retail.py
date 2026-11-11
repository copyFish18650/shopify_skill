#!/usr/bin/env python3
"""Add native catalog navigation and small retail affordances to this skill's own base."""
import argparse,json,re,shutil
from pathlib import Path

ASSETS=Path(__file__).resolve().parents[1]/'assets/retail-native'

def apply_native_retail(theme,category_labels=None,nav_style='underline',link_feedback='line',media_feedback='none',dialog_feedback='fade'):
    theme=Path(theme).resolve()
    def read(name):return (theme/name).read_text(encoding='utf-8')
    def write(name,text):(theme/name).write_text(text,encoding='utf-8')
    def load(name):return json.loads(read(name))
    def save(name,value):write(name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    source=read('sections/header.liquid')
    if 'data-catalog-header' in source:return {'already_applied':True,'theme_dir':str(theme)}
    # Do not replace arbitrary merchant headers with this base-specific adapter.
    for marker in ['<nav class="desktop-nav"',"{% render 'localization', location: 'mobile-header' %}",'<div class="header-actions">']:
        if marker not in source:raise ValueError('Not a compatible native header: '+marker)
    settings=[
      {'type':'checkbox','id':'show_catalog_navigation','label':'Show automatic categories','default':True},
      {'type':'select','id':'catalog_source','label':'Category navigation source','default':'auto','options':[{'value':'auto','label':'Store collections, then types'},{'value':'blocks','label':'Category blocks'}]},
      {'type':'range','id':'catalog_limit','label':'Maximum category links','min':2,'max':12,'step':1,'default':6},
      {'type':'checkbox','id':'catalog_placeholders','label':'Show planned labels in empty store','default':True,'info':'Labels have no link until matching store data exists. Importing products replaces them automatically.'},
      {'type':'checkbox','id':'catalog_mobile_bar','label':'Show mobile category shortcuts','default':True},
      {'type':'select','id':'catalog_nav_style','label':'Navigation feedback','default':nav_style,'options':[{'value':'underline','label':'Underline'},{'value':'rule','label':'Top rule'},{'value':'pill','label':'Soft field'},{'value':'index','label':'Directional index'}]}
    ]
    block={'type':'catalog_category','name':'Category navigation','settings':[{'type':'text','id':'label','label':'Display label'},{'type':'collection','id':'collection','label':'Collection in block mode'},{'type':'text','id':'product_type','label':'Exact product type in block mode'}]}
    labels=[str(label).strip() for label in category_labels or [] if str(label).strip()][:12]
    match=re.search(r'{% schema %}([\s\S]*?){% endschema %}',source);schema=json.loads(match[1]);schema['settings']+=settings;schema.setdefault('blocks',[]).append(block);schema['max_blocks']=12
    for preset in schema.get('presets',[]):
        if labels:preset['blocks']=[{'type':'catalog_category','settings':{'label':label}} for label in labels]
    capture="""{% capture catalog_navigation %}{% if section.settings.show_catalog_navigation %}{% render 'catalog-navigation', dedupe_menu:true %}{% endif %}{% endcapture %}{% assign catalog_navigation = catalog_navigation | strip %}
{% capture catalog_shortcuts %}{% if section.settings.show_catalog_navigation %}{% render 'catalog-navigation', dedupe_menu:false %}{% endif %}{% endcapture %}{% assign catalog_shortcuts = catalog_shortcuts | strip %}
"""
    markup=source[:match.start()]
    markup=capture+markup.replace('<header class="site-header','<header data-catalog-header data-nav-style="{{ section.settings.catalog_nav_style }}" class="site-header catalog-header',1)
    mobile="""{% if catalog_navigation != blank %}<div class="mobile-catalog-group"><p>{{ 'navigation.categories' | t }}</p>{{ catalog_navigation }}</div>{% endif %}
"""
    marker="{% if shop.customer_accounts_enabled %}<a href=\"{{ routes.account_url }}\">"
    if marker not in markup:raise ValueError('Native mobile account insertion point missing')
    markup=markup.replace(marker,mobile+marker,1)
    # Keep every existing menu link and nested destination; only append real categories.
    nav_start=markup.index('<nav class="desktop-nav"');nav_end=markup.index('</nav>',nav_start)
    markup=markup[:nav_end]+'{{ catalog_navigation }}\n'+markup[nav_end:]
    fallback="{% if section.settings.menu.links == blank %}<a href=\"{{ routes.all_products_collection_url }}\">{{ section.settings.fallback_label | escape }}</a>{% endif %}"
    markup=markup.replace(fallback,"{% if section.settings.menu.links == blank %}<a href=\"{{ routes.root_url }}\"{% if request.page_type == 'index' %} aria-current=\"page\"{% endif %}>{{ 'navigation.home' | t }}</a><a href=\"{{ routes.all_products_collection_url }}\">{{ section.settings.fallback_label | escape }}</a>{% endif %}")
    shortcuts="""{% if section.settings.catalog_mobile_bar and catalog_shortcuts != blank %}<nav class="catalog-shortcuts" aria-label="{{ 'navigation.categories' | t }}"><div class="container catalog-shortcuts__inner">{{ catalog_shortcuts }}</div></nav>{% endif %}
"""
    markup=markup.replace('</header>',shortcuts+'</header>',1)
    write('sections/header.liquid',markup+'\n{% schema %}\n'+json.dumps(schema,ensure_ascii=False,indent=2)+'\n{% endschema %}\n')
    group=load('sections/header-group.json');header=next(x for x in group['sections'].values() if x['type']=='header')
    header.setdefault('settings',{}).update({field['id']:field['default'] for field in settings})
    if labels:
        header.setdefault('blocks',{});header.setdefault('block_order',[])
        for i,label in enumerate(labels,1):
            key='catalog_'+str(i);header['blocks'][key]={'type':'catalog_category','settings':{'label':label}};header['block_order'].append(key)
    save('sections/header-group.json',group)
    for name in ['catalog-navigation.liquid','retail-image-dialog.liquid']:shutil.copyfile(ASSETS/name,theme/'snippets'/name)
    for name in ['retail-native.css','retail-native.js']:shutil.copyfile(ASSETS/name,theme/'assets'/name)
    definitions=[
      {'type':'checkbox','id':'enable_micro_motion','label':'Enable small motion feedback','default':True},
      {'type':'select','id':'link_feedback','label':'Link and button feedback','default':link_feedback,'options':[{'value':'line','label':'Growing rule'},{'value':'fill','label':'Inset field'},{'value':'bracket','label':'Fine frame'}]},
      {'type':'select','id':'media_feedback','label':'Media feedback','default':media_feedback,'options':[{'value':'none','label':'Keep photos still'},{'value':'zoom','label':'Subtle zoom'},{'value':'lift','label':'Category image lift'},{'value':'frame','label':'Product edge accent'}]},
      {'type':'select','id':'dialog_feedback','label':'Cart drawer entrance','default':dialog_feedback,'options':[{'value':'fade','label':'Fade'},{'value':'slide','label':'Short slide'}]},
      {'type':'checkbox','id':'enable_image_zoom','label':'Enable product image viewer','default':True},
      {'type':'checkbox','id':'enable_quantity_buttons','label':'Product quantity buttons','default':True}
    ]
    schema=load('config/settings_schema.json');schema.append({'name':'Interaction details','settings':definitions});save('config/settings_schema.json',schema)
    data=load('config/settings_data.json');values={f['id']:f['default'] for f in definitions};data['current'].update(values)
    for preset in data.get('presets',{}).values():preset.update(values)
    save('config/settings_data.json',data)
    locale=load('locales/en.default.json');locale['navigation']={'home':'Home','categories':'Browse categories','awaiting_catalog':'Category preview — available after products are imported'};locale['retail']={'enlarge_image':'Enlarge product photo','image_viewer':'Product photo viewer','image_error':'This photo could not be loaded. Close this window to continue.','quantity_decrease':'Decrease quantity','quantity_increase':'Increase quantity'};save('locales/en.default.json',locale)
    layout=read('layout/theme.liquid');layout=layout.replace('</head>',"{{ 'retail-native.css' | asset_url | stylesheet_tag }}\n<script src=\"{{ 'retail-native.js' | asset_url }}\" defer=\"defer\"></script>\n</head>",1)
    layout=layout.replace('<body ','''<body data-retail-ui data-link-feedback="{{ settings.link_feedback }}" data-media-feedback="{{ settings.media_feedback }}" data-dialog-feedback="{{ settings.dialog_feedback }}" data-quantity-buttons="{{ settings.enable_quantity_buttons }}" data-quantity-decrease="{{ 'retail.quantity_decrease' | t | escape }}" data-quantity-increase="{{ 'retail.quantity_increase' | t | escape }}" ''',1)
    layout=re.sub(r'(<body\b[^>]*class=")',r'\1{% if settings.enable_micro_motion %}retail-motion {% endif %}',layout,count=1)
    layout=layout.replace('</body>',"{% render 'retail-image-dialog' %}\n</body>",1);write('layout/theme.liquid',layout)
    product=read('sections/main-product.liquid')
    zoom='''{% if settings.enable_image_zoom %}<a class="retail-image-open" data-retail-image-open data-image-alt="{{ media_alt | escape }}" href="{{ media | image_url: width:2400 }}" target="_blank" rel="noopener" aria-label="{{ 'retail.enlarge_image' | t }}">{% render 'icon',name:'search' %}<span>{{ 'retail.enlarge_image' | t }}</span></a>{% endif %}'''
    product,count=re.subn(r"(\{% when 'image' %\}[\s\S]*?)(\{% when 'video' %\})",lambda m:m[1]+zoom+m[2],product,count=1)
    if count!=1:raise ValueError('Native product image insertion point missing')
    write('sections/main-product.liquid',product)
    return {'theme_dir':str(theme),'planned_category_labels':labels,'automatic_navigation':'collections then types; native menus preserved; no backend menu creation','micro_motion':values,'nav_style':nav_style}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('theme_dir',type=Path);p.add_argument('--category-label',action='append',default=[]);p.add_argument('--nav-style',default='underline',choices=['underline','rule','pill','index']);args=p.parse_args()
    print(json.dumps(apply_native_retail(args.theme_dir,args.category_label,args.nav_style),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
