# 首页占位与 CSV 导入后的自动展示

## 店主要求的流程

主题 ZIP 导入空店后，首页已经有商品区和分类区的位置。完全没有可见商品时，前台显示明确的待导入卡片，默认 8 个商品位、4 个分类位；不是只在编辑器中显示，也不能把整块目录隐藏。占位使用中性图形，没有虚假商品、价格、库存、评分、购买按钮或假链接。

CSV 导入后，刷新首页即可读取 Shopify 真实数据，不需要重新生成 ZIP、修改代码或手动绑定 All products。真实商品出现后移除占位，只显示实际数量，不以假卡填满行。店主可在编辑器关闭空占位、修改标题与数量、替换集合或隐藏模块。

这是数据流程，不固定首页版式。商品/分类入口的顺序、卡片媒体比例、分区、标题和分类构成按本次设计决定；默认主商品网格仍为桌面 4/手机 2 列。不能为“自由设计”把首页购物内容删掉或藏到冗长叙事之后。

## 原生数据规则

- 商品区默认 `section.settings.collection | default: collections.all`，读取真实 `products`；仅在店主明确选择特定集合时使用该集合。卡片保留真实标题、价格、图片、变体与快速购买。无图片的真实商品可用中性图片缺失图形，不能从场景图伪造商品图片。
- 分类区默认自动模式：遍历真实可见且有商品的集合，排除系统 All / frontpage 默认入口，按配置数量显示。集合图片使用 `collection.featured_image`，没有单独集合图时 Shopify 可回退首件商品图。CSV 的 `Collection` 列可把商品加入实际集合，集合不存在时由 Shopify 导入器创建；主题本身不创建集合记录。
- 没有可用集合时使用 `collections.all.all_types`，忽略空 Type。标题用真实 Type，图片取该类型实际商品图；链接使用原生 `/collections/types?q=...`（`routes.collections_url` 加 `/types`，仅编码查询值），或 Shopify `link_to_type`。不要依赖店主尚未启用的集合筛选器来构造入口。
- 产品既无集合又无 Type 时，仍展示真实商品和一个真实 All products 分类入口。不从产品标题、图片或 Shopify 标准 Product category 擅自猜测集合。
- 手选模式通过 collection blocks 提供明确覆盖；默认自动模式不能依赖店主先手选集合。空集合不输出假栏目。

## Header 与首页分类联动

默认把真实分类同时接入 Header，不能只完成首页中段图卡。店主导入 CSV 后，头部集合/Type 链接随原生数据自动出现；不需要重新生成主题或先配置后台主菜单。保留现有菜单标签、排序和全部嵌套链接，按精确目的地去重追加分类；默认 Home/Catalog/Contact 菜单也不能导致自动分类被跳过。

桌面优先形成品牌、横向导航、搜索/账户/购物车的清楚关系；长店名或分类多时合理换行、分组或提供完整浏览去向，不压缩到不可读。手机同时提供紧凑分类捷径和完整菜单，触控/键盘可用。真实集合用其原生 url，Type 用 routes.collections_url + /types?q=编码值；不拼接来源域名或不存在的 /collections/handle。

空店可以用当前品类规划的可编辑标签预览导航，但应是明确不可点击的 span / aria-disabled，没有假分类链接；导入真实集合/Type 后自动替换。已经有商品但没有任何分类时保留真实 All products 去向，不把计划标签冒充实际分类。后续导入不同目录也须读当前店数据，不能把上次采集目录写死为唯一导航。

提供编辑器开关、自动/明确选择方式及适量配置。使用本技能基线时，prepare_theme.py 已接入 apply_native_retail.py；可用重复 --category-label 参数传入本次计划标签。功能 helper 不适配任意原主题，不用于替换店主已有 Header。布局与动效按本次独立设计继续改写。

CSV 的 Collection 列和主题动态渲染不能创建后台 Menus 记录。顶部主分类可分层组织，不要求把全站上百个分类平铺成一行；完整分类仍须有真实可达的浏览路径，明确原生循环限制与实际覆盖范围。

## CSV 与可见性说明

商品须为 active 并发布到 Online Store，主题只能显示店面有权读取的产品。现有 CSV 模板中的旧列名 Shopify 保持兼容；处理实际 CSV 前查当前官方字段，不凭空改动用户变体列或库存设置。

本流程的带商品成品必须同时完成 `Product category`、`Type` 与主 `Collection`／真实分类关联，按 [商品类别与库存完整性](catalog-completeness.md) 核对；不是三选一。标准类别不负责首页购物导航，库存也不由主题控制。`Collection` 是导入器支持的额外列，每个产品最多通过这一列指定一个集合；已有自动集合仍需满足其条件。`Type` 是自定义产品类型，与标准 Product category 不相同。都不填时商品仍可显示，只回退全部商品入口。产品图片来自 CSV 导入后的真实商品媒体，主题 ZIP 无法使缺失的图片 URL 自动有效。

核对 [CSV 字段与 Collection 规则](https://help.shopify.com/en/manual/products/import-export/using-csv)、[导入与发布到 Online Store](https://help.shopify.com/en/manual/products/import-export/import-products)、[collection.all_types / current_type](https://shopify.dev/docs/api/liquid/objects/collection)、[link_to_type](https://shopify.dev/docs/api/liquid/filters/link_to_type)。这些规则在 2026-10-26 已查询，实际任务仍以当前官方说明与店铺配置为准。

## 抓取目录后的两文件交付

先执行 [source-catalog.md](source-catalog.md) 的全目录、可售变体与图片核对；这里处理导入后的展示关联。

需要抓取商品和分类时，把可运行主题与可导入商品分别交付为主题 ZIP 和独立 CSV，不默认再打整合素材包。CSV 要含实际商品、变体、价格、图片 URL 与分类关联，主题要读取这些数据；不能把另一个分类 JSON、图片 ZIP 或操作脚本作为完成前台展示的必需第三份文件。

用户明确要多份目录时可为同站交付 csv1.csv…csv5.csv 等指定份数，各份保持本站同品类、各有不同选品；主题读取真实导入数据，不绑定某份 CSV 文件名。保留既有文件名和份数，逐份验证商品／规格／图片／分类及 [逐站折扣定价](pricing-and-promotions.md)，不能只检查第一份或把同一目录复制五遍。

单一主集合可用 Collection 列；原站商品属于多个分类时，可把完整关联编码到 CSV 的商品标签，并把对应的名称映射与原生筛选逻辑放入主题，使导入后可直接分类浏览。验证标签数、循环、索引和目标页，避免静默截断。明确这种前台分类视图与后台独立集合记录的区别，不宣称 ZIP 创建了后台集合或导航菜单。

分类标签采用稳定命名空间和无冲突的 handle，链接通过本地化集合路由与实际标签构造，例如 All products 的标签视图。分类标题读取包内名称映射，不能把机器标签直接显示为顾客标题；分类页读取当前真实集合及 current_tags，保留分页、排序和产品表单。未有对应可见商品时保持空店/原生集合/Type 回退，不能仅凭采集时的数量显示假分类。

Liquid 单个 for 循环最多 50 次。大量已知映射可分块渲染；支持分页的数据用适当 paginate。不要对一个长 split 数组加大 limit 就当作已解决，也不要假设读取全部 tags/types 的对象没有自身上限。用接近实际规模的运行时数据核对分类总数和每个分块边界；本地 Liquid 引擎可能更宽松，需模拟平台限制或明确未验证限制。对原生数据对象的截断/访问上限另行核实，不用分块掩盖缺失数据。实现参考：[Liquid for](https://shopify.dev/docs/api/liquid/tags/for)、[原生 tag filtering](https://shopify.dev/docs/storefronts/themes/navigation-search/filtering/tag-filtering)。

商品图片使用交付时已核对可访问的 HTTP(S) URL，由 Shopify 随 CSV 导入；本地图片副本不能作为 CSV 图片路径。主题首屏和必要场景图仍压缩后放入 assets。已下载的全量商品图片、原始数据和映射清单可以留在本地工作目录，不需放进主题 ZIP，也不需让店主上传图片备份包；额外离线归档仅在用户明确要求时交付。

## 验收

用同一份保存的首页配置验证空店、实际集合、仅 Type、无分类、单件、多变体和售罄状态。空占位不能购买；有商品后卡片和分类自动替换；Type 查询中的空格、与号等正确编码；分类目标页显示相应商品。桌面商品 4 列、手机 2 列，分类和商品区都无溢出。保留 Footer / 政策和购物车回归检查。

本地可用隔离 Shopify 对象模拟导入前后状态，但应明确这不是实际向店铺导入 CSV。未获用户授权时不上传测试商品；不能把本地模拟通过写成真实 CSV 导入成功。

另验 Header 实际出现相同分类及正确目标，覆盖空主菜单、默认主菜单、已含分类和嵌套去重，检查手机捷径、完整菜单、长名称与本地化。空店计划标签不能点击到 404；所有真实分类状态与首页数据一致。
