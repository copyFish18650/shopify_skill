#!/usr/bin/env python3
"""Progressively enhance this skill's native base; preserve live Shopify objects/forms/settings."""
import argparse,json,re,shutil
from pathlib import Path
ASSETS=Path(__file__).resolve().parents[1]/'assets/retail-native'

def neutralize_base_copy(theme):
    """Replace only exact, known seed copy; keep IDs, native data and custom merchant copy."""
    theme=Path(theme)
    replacements={
      'Find your next pair.':'Explore the collections.',
      '<p>Questions about sizing, an order, or your next pair? Send us a message.</p>':'<p>Questions about an item or an order? Send us a message.</p>',
      'Sizing & fit':'Product details & dimensions',
      '<p>Check the size information for this product before ordering. Sizing may vary by style. If you are unsure, contact us before choosing your size.</p>':'<p>Check the listed dimensions, materials, compatibility, and available options for this item before ordering. Contact support if you need a detail before choosing.</p>'
    }
    def values(v):
        if isinstance(v,dict):return {k:values(x) for k,x in v.items()}
        if isinstance(v,list):return [values(x) for x in v]
        return replacements.get(v,v) if isinstance(v,str) else v
    for name in ['templates/page.contact.json','templates/list-collections.json','templates/product.json']:
        p=theme/name;old=json.loads(p.read_text(encoding='utf-8'));new=values(old)
        if new!=old:p.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name in ['sections/contact.liquid','sections/main-list-collections.liquid']:
        p=theme/name;s=p.read_text(encoding='utf-8');m=re.search(r'{% schema %}([\s\S]*?){% endschema %}',s);old=json.loads(m[1]);new=values(old)
        if new!=old:p.write_text(s[:m.start()]+'{% schema %}\n'+json.dumps(new,ensure_ascii=False,indent=2)+'\n{% endschema %}\n',encoding='utf-8')
    p=theme/'locales/en.default.json';v=json.loads(p.read_text(encoding='utf-8'))
    if v['general'].get('search_prompt')=='Find your next pair.':v['general']['search_prompt']='What are you looking for?'
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def apply_storefront_depth(theme,control_style='line',tone='editorial',gallery='paired',mega_label='Explore the store',bundled_editorial=False):
    theme=Path(theme).resolve()
    def read(n):return (theme/n).read_text(encoding='utf-8')
    def write(n,s):(theme/n).write_text(s,encoding='utf-8')
    def load(n):return json.loads(read(n))
    def save(n,v):write(n,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
    layout=read('layout/theme.liquid')
    if 'storefront-depth.css' in layout:return {'already_applied':True,'theme_dir':str(theme)}
    if 'data-catalog-header' not in read('sections/header.liquid'):raise ValueError('Apply native retail adapter first; this adapter does not replace arbitrary merchant themes.')
    for n in ['catalog-controls.css','catalog-controls.js','storefront-depth.css','storefront-depth.js']:shutil.copy2(ASSETS/n,theme/'assets'/n)
    for n in ['catalog-filter-values.liquid','store-discovery.liquid','collection-context-navigation.liquid']:shutil.copy2(ASSETS/n,theme/'snippets'/n)
    shutil.copy2(ASSETS/'catalog-filters.liquid',theme/'snippets/filters.liquid')
    editorial=(ASSETS/'editorial-assortment.liquid').read_text(encoding='utf-8')
    if not bundled_editorial:
        editorial=editorial.replace('section.settings.image != blank or section.settings.use_bundled_image','section.settings.image != blank')
        editorial=re.sub(r'{% elsif section.settings.use_bundled_image %}[\s\S]*?{% endif %}','{% endif %}',editorial,count=1)
        em=re.search(r'{% schema %}([\s\S]*?){% endschema %}',editorial);es=json.loads(em[1]);es['settings']=[f for f in es['settings'] if f.get('id')!='use_bundled_image']
        editorial=editorial[:em.start()]+'{% schema %}\n'+json.dumps(es,ensure_ascii=False,indent=2)+'\n{% endschema %}\n'
    write('sections/editorial-assortment.liquid',editorial)
    icon=read('snippets/icon.liquid')
    if "when 'filter'" not in icon:write('snippets/icon.liquid',icon.replace('{% endcase %}',"{% when 'filter' %}<path d=\"M4 7h16M4 17h16\"/><circle cx=\"9\" cy=\"7\" r=\"2\" fill=\"var(--bg,white)\"/><circle cx=\"15\" cy=\"17\" r=\"2\" fill=\"var(--bg,white)\"/>{% endcase %}"))
    fields=[
      {'type':'checkbox','id':'show_result_count','label':'Show labeled result count','default':True},
      {'type':'select','id':'catalog_control_style','label':'Catalog toolbar','default':control_style,'options':[{'value':'line','label':'Fine rule'},{'value':'panel','label':'Inset panel'},{'value':'rail','label':'Compact rail'}]},
      {'type':'checkbox','id':'catalog_controls_sticky','label':'Keep catalog controls in view','default':False},
      {'type':'select','id':'storefront_tone','label':'Interior page composition','default':tone,'options':[{'value':'editorial','label':'Editorial'},{'value':'framed','label':'Framed'},{'value':'compact','label':'Compact'}]},
      {'type':'select','id':'product_gallery_style','label':'Product photo layout','default':gallery,'options':[{'value':'paired','label':'Paired photos'},{'value':'focus','label':'Focus with thumbnails'},{'value':'stacked','label':'Stacked photos'}]},
      {'type':'checkbox','id':'variant_choice_buttons','label':'Buttons for short variant lists','default':True,'info':'Uses real variants; longer lists keep the native select.'}
    ]
    schema=load('config/settings_schema.json');schema.append({'name':'Storefront pages','settings':fields});save('config/settings_schema.json',schema)
    data=load('config/settings_data.json');values={f['id']:f['default'] for f in fields};data['current'].update(values)
    for p in data.get('presets',{}).values():p.update(values)
    save('config/settings_data.json',data)
    layout=layout.replace('</head>',"{{ 'catalog-controls.css' | asset_url | stylesheet_tag }}\n{{ 'storefront-depth.css' | asset_url | stylesheet_tag }}\n<script src=\"{{ 'catalog-controls.js' | asset_url }}\" defer=\"defer\"></script>\n<script src=\"{{ 'storefront-depth.js' | asset_url }}\" defer=\"defer\"></script>\n</head>",1)
    layout=layout.replace('<body ','<body data-storefront-tone="{{ settings.storefront_tone }}" ',1);write('layout/theme.liquid',layout)
    def section_update(name,mutate,fields=None):
        source=read('sections/'+name+'.liquid');m=re.search(r'{% schema %}([\s\S]*?){% endschema %}',source)
        record=json.loads(m[1]);body=mutate(source[:m.start()])
        if fields:record['settings']+=fields
        write('sections/'+name+'.liquid',body+'\n{% schema %}\n'+json.dumps(record,ensure_ascii=False,indent=2)+'\n{% endschema %}\n')
    crumb="""<nav class="store-breadcrumbs" aria-label="{{ 'storefront.breadcrumbs' | t }}"><a href="{{ routes.root_url }}">{{ 'navigation.home' | t }}</a><span aria-hidden="true">/</span><a href="{{ routes.all_products_collection_url }}">{{ 'general.view_all' | t }}</a></nav>"""
    def collection(s):
        s=s.replace('class="page-space ','class="page-space store-collection-page ',1).replace('<div class="page-heading">',crumb+'<div class="page-heading">',1)
        if '<nav class="catalog-topics"' in s:
            start=s.index('<nav class="catalog-topics"');end=s.index('</nav>',start)+len('</nav>')
            s=s[:start]+"{% render 'collection-context-navigation' %}{% if section.settings.show_source_topics %}"+s[start:end]+"{% endif %}"+s[end:]
        else:s=s.replace('<div class="collection-toolbar">',"{% render 'collection-context-navigation' %}<div class=\"collection-toolbar\">",1)
        return s
    section_update('main-collection',collection,[{'type':'checkbox','id':'show_source_topics','label':'Show source tag shortcuts','default':False,'info':'Optional imported source catalog tags; store collections and types appear above by default.'}])
    def search(s):
        s=s.replace('class="page-space ','class="page-space store-search-page ',1).replace('<div class="page-heading">',crumb+'<div class="page-heading">',1)
        marker='{% if search.performed %}{% paginate'
        s=s.replace(marker,"{% unless search.performed %}<h2 class=\"discovery-heading\">{{ 'navigation.categories' | t }}</h2>{% render 'store-discovery' %}{% endunless %}"+marker,1)
        return s
    section_update('main-search',search)
    service="""<div class="product-service-links"><a href="#StoreInformation" data-store-policy="shipping">{{ 'storefront.delivery' | t }}{% render 'icon',name:'arrow' %}</a><a href="#StoreInformation" data-store-policy="returns">{{ 'storefront.returns' | t }}{% render 'icon',name:'arrow' %}</a></div>"""
    def product(s):
        s=s.replace('class="page-space ','class="page-space store-product-page ',1).replace('<div class="product-gallery">','<div class="product-breadcrumb-slot">'+crumb+'</div><div class="product-gallery" data-product-gallery="{{ settings.product_gallery_style }}" data-gallery-label="{{ \'storefront.product_photos\' | t }}" data-photo-label="{{ \'storefront.photo\' | t }}">',1)
        s=s.replace('<div class="product-media">','<div class="product-media" data-media-type="{{ media.media_type }}">')
        s=s.replace('data-product-section>','data-product-section data-variant-buttons="{{ settings.variant_choice_buttons }}">',1)
        s=s.replace('{% endform %}','{% endform %}'+service,1)
        return s
    section_update('main-product',product)
    def cart(s):
        s=s.replace('class="page-space ','class="page-space store-cart-page ',1).replace('<div class="page-heading">',crumb+'<div class="page-heading">',1)
        s=s.replace("{{ 'cart.title' | t }}</h1></div>","{{ 'cart.title' | t }}</h1><a href=\"{{ routes.all_products_collection_url }}\">{{ 'general.continue_shopping' | t }} ↗</a></div>",1)
        s=s.replace('{% endform %}','{% endform %}'+service,1)
        s=s.replace("{% endif %}</div></section>","{% endif %}{% if cart.item_count == 0 and collections.all.products_count > 0 %}<h2 class=\"discovery-heading\">{{ 'navigation.categories' | t }}</h2>{% render 'store-discovery' %}{% endif %}</div></section>",1)
        return s
    section_update('main-cart',cart)
    for n in ['main-page','contact','main-blog','main-article','main-list-collections','main-404','main-account','main-addresses','main-login','main-register','main-order','main-activate_account','main-reset_password','main-password']:
        p=theme/'sections'/(n+'.liquid')
        if p.exists():
            s=p.read_text(encoding='utf-8');s=s.replace('class="page-space ','class="page-space store-content-page ',1);p.write_text(s,encoding='utf-8')
    footer=read('sections/footer.liquid');footer=footer.replace('<div class="container">','<span id="StoreInformation" class="visually-hidden"></span><div class="container">',1)
    footer=footer.replace('<a href="{{ document_url }}">','<a data-policy-kind="{{ block.settings.kind }}" href="{{ document_url }}">').replace('<a href="#InformationContent-','<a data-policy-kind="{{ block.settings.kind }}" href="#InformationContent-')
    write('sections/footer.liquid',footer)
    mega="""{% if section.settings.show_department_panel and collections.all.products_count > 0 %}<details class="nav-dropdown department-mega"><summary>{{ section.settings.department_label | escape }}</summary><div class="department-mega__panel"><div class="department-mega__head"><h2>{{ 'navigation.categories' | t }}</h2><a href="{{ routes.all_products_collection_url }}">{{ 'general.view_all' | t }}{% render 'icon',name:'arrow' %}</a></div>{% render 'store-discovery' %}</div></details>{% endif %}"""
    def header(s):
        start=s.index('<nav class="desktop-nav"');end=s.index('</nav>',start);return s[:end]+mega+s[end:]
    section_update('header',header,[{'type':'checkbox','id':'show_department_panel','label':'Show image department menu','default':True},{'type':'text','id':'department_label','label':'Department menu label','default':mega_label}])
    g=load('sections/header-group.json')
    for r in g['sections'].values():
        if r['type']=='header':r.setdefault('settings',{}).update({'show_department_panel':True,'department_label':mega_label})
    save('sections/header-group.json',g)
    locale=load('locales/en.default.json');locale['catalog_controls']={'product':'product','products':'products','result':'result','results':'results','filter_sort':'Filter & sort','price_currency':'Prices in','min':'Minimum','max':'Maximum','invalid_price':'The maximum must be greater than or equal to the minimum.','apply':'Apply','reset_group':'Reset','sort':'Sort by','draft':'Apply to update the selection.','updating':'Updating…','view_results':'View results','clear':'Clear filters','active':'Applied filters'}
    locale['storefront']={'breadcrumbs':'Breadcrumbs','delivery':'Delivery information','returns':'Returns & support','product_photos':'Product photos','photo':'View photo','edit_empty':'Select a collection with more products or reduce the offset.'}
    locale['cart']['empty']='There’s room for something useful.'
    locale['contact']['intro']='Questions about an item or an order? Send us a message.'
    locale['general']['search_placeholder']='Search products and more'
    locale['product']['size']='Product information';locale['product']['size_help']='Check the listed details, dimensions, and available options for the selected item.'
    save('locales/en.default.json',locale)
    neutralize_base_copy(theme)
    return {'theme_dir':str(theme),'controls':control_style,'interior_composition':tone,'gallery':gallery,'mega_menu':mega_label,'backend_mutations':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('theme_dir',type=Path);a=p.parse_args();print(json.dumps(apply_storefront_depth(a.theme_dir),ensure_ascii=False,indent=2))
