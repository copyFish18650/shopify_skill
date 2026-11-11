# 参考梳理与无原主题构建

基础站按 [basic-store-standard.md](basic-store-standard.md)，精品站按 [premium-store-standard.md](premium-store-standard.md) 核对各自基准的完整度与适用组件。精品优先沿用用户认可的历史精品，无具体指明时用 Cozyster，按约 85% 成熟结构／15% 局部适配实施，允许导航、卡片、详情与页面节奏复用；基础与自主模式保持实质结构差异。各模式执行 [site-diversity.md](site-diversity.md) 的图像唯一，实际看参考及成品，功能底稿检查不代替视觉与交互验收。

## 自动开始的判断

开始下述本地构建前先完成 [三技能准备](design-skill-prerequisites.md)；“自动开始”指安装核对和规则读取完成后继续自主执行，不是跳过前置准备先写主题。缺项先解决，不能用已有功能骨架绕过该顺序。

用户输入品类并要求装修，即已授权本地设计、创建主题文件、图片和 ZIP。不要把没有原主题、文件夹为空、参考站不能访问、没有店铺连接或品牌资料未齐当作暂停本地工作的常规理由。缺品牌用 Shopify 原生 shop 信息，缺经营事实在 ZIP 内可编辑正文中标记 #待填入，缺预览则诚实区分静态与线上验证。

有用户指定的原主题时在副本上改；无原主题时自己编写 Shopify 原生 Online Store 2.0 主题。用户明确不希望使用官方主题，不自动下载、克隆或换皮 Dawn / Horizon 等主题。可以查 Shopify 官方开发文档以正确实现平台功能；查文档不等于套用官方主题。

原任务已明确了品类、市场、结构和审美时，不重复询问是否开始、是否可以自己建主题、要哪一种固定模板。合理设计选择直接执行。只有实际不可用的工具、必要事实或明确范围冲突才提出具体问题，同时继续独立工作；不得凭空声称已完成受阻的检查。

## 复用已经运行的自编功能骨架

无用户原主题时，从本技能 `assets/native-base.zip` 创建工作副本。该包是独立编写的 Stride Atelier 目录版 04，未套用官方主题，包含完整原生模板、真实 Shopify 数据与表单接入、Footer group、14 份可编辑内置文档，以及空店占位 / CSV 导入后商品分类自动展示流程。使用相对技能目录的命令：

```text
python scripts/prepare_theme.py --category "本次实际品类" --operator-name "本次经营者姓名" --operator-address "本次证件地址（街道、城市、州/省、邮编、国家）" --output "output/shopify/本次唯一目录/theme"
```

脚本核对基线哈希与 ZIP 完整性，拒绝覆盖已有目录；不连接店铺、不发布。用户提供原主题时仍在其副本上改，不用此骨架替换用户主题。

新版 prepare_theme.py 在临时副本中自动应用 [用户确认的政策底稿](merchant-policy-defaults.md)：更新 14 份包内正文、Footer defaults/presets 与保存 blocks、相关 FAQ，再执行静态检查后复制到新目录。原 native-base.zip 及来源哈希保持不变。新正文不是旧草稿的线上验证证据，生成时仍核对本次品类、实际后台优先政策及运行结果。后续若重写 Footer，不得从旧项目复制回过时条款。

这十四份是可编辑草稿，不是必须可见的 Footer 清单。精品严格复刻须再按本次参考截图调整列、名称、数量、顺序、布局和开关；本次 Cozyster 图2的四列／十链接及 Newsletter 开启覆盖底稿的旧展示默认，详见 [Footer 严格复刻规则](footer-and-policies.md#精品严格复刻的可见-footer)。未展示的必要正文隐藏归档，不因减少可见链接而丢弃；准备脚本本身不等于已完成该截图还原。

脚本在种入正文、零售和整站功能后，还自动执行 `apply_native_service_pages.py`：移除旧基线的 Footer 政策弹窗、按目标去重，接入真实 Page／Policy 解析、Page 模板／阅读样式、内容清单和原生本地化控件。它只适配本技能新建副本，不用来整体覆盖店主现有 Footer；不创建后台 Pages、不改变 Markets 或商品价格。仅模板时保存中性公告且不宣称促销；先在工作目录保存本站从 10%、15%、20%、25% 四档随机选定的固定折扣计划，全部 CSV 按其倍率核对后可传 `--promotion-ready --announcement-text "本站准确折扣文案"`。

最后改完品类指南、政策标题／正文、地址或 Footer 保存块后，打包前运行：

```text
python scripts/apply_native_service_pages.py "THEME_DIR" --refresh-manifest-only
```

该模式从当前 Footer 刷新 `assets/service-pages-manifest.json`，保留已自主设计的 Footer、CSS、本地化组件及公告状态。实际商品价格已按 [pricing-and-promotions.md](pricing-and-promotions.md) 验证后，可追加 `--promotion-ready --announcement-text "15% off your everyday selection"` 启用本次公告；按站点调整措辞。清单来源哈希标记真正的源底稿，最终交付 ZIP 的哈希写在外部交付记录，不能在包内伪造自身哈希。Page 正文后续在后台单独维护。

--operator-name 仅传入本次允许公开的个人经营者姓名，脚本会对正文插值做 HTML 转义；缺姓名时保留一个待填，不以店名或来源站经营者猜测填充。--operator-address 传入本站本次证件或按证件整理的完整地址，保留正确换行；脚本写入 Footer 的共享 operator_address 设置，渲染时 HTML 转义，并供 Footer / 内置 Contact Information / Legal Notice 共用。缺地址保留 #待填入；账户邮箱仍不作客服邮箱，不自动把联系地址作为退货目的地。联系表单前台功能与后台实际收件设置分别验收。

脚本还在自己的新副本中调用 apply_native_retail.py，接通 Header 的真实集合/Type 导航、手机分类捷径与少量原生零售操作。重复 --category-label "本次计划分类" 可给空店设置不可点击预览；导入后自动读真实数据。它保留已有菜单，不创建后台 Menus。assets/retail-native 是功能组件，不是固定展示答案；按 [CSS 交互知识库](css-interaction-knowledge.md) 与本次设计改写外观、选取不同反馈，并重新实测。新组件没有继承旧基线的线上验证结论。

基线来自鞋履项目：其中的鞋履图片、首页、FAQ、尺码指南、退换和售后术语、locale 文案、schema defaults / presets 与保存 JSON 均须按本次品类核对。更换至少两张符合本次品类且与其他站不同源的互联网真实照片，登记全部轮播帧、场景／专题图及其桌面／手机素材族；按 site-diversity 对本批和已登记历史查重，不能沿用基线或前项目激活图／重加模块默认图。同时更新全部响应式尺寸和手机裁切；默认不自行生成，逐张筛除明显品牌标识、文字及水印，并记录来源与使用依据。基线的店名来自 `shop.name`，不能把 Stride Atelier 当成新店品牌。

把 `native-base.zip` 视为功能实现参考，而非精品视觉答案。精品展示层优先从用户认可的成熟精品基准保留和适配，不因使用功能底稿而退回其简单外观，也不强制重写已成熟的布局；基础与自主模式再按各自规则决定首屏、购物入口和节奏。需要改动时同步 Liquid/HTML、schema、保存 JSON 与 CSS，保护原生数据、表单和 Footer 依赖。先查历史再看实际截图；功能通过不能替代视觉验收，精品不因版式相近被强制重做。

基线验证范围见 `assets/native-base.json`：原 03 版首页、Footer 分组与物流 / 售后 / 退换阅读窗口在 Shopify 草稿中实际观察过；04 版页脚文件与之相同。04 版共 79 项本地行为检查，含 27 项空店 / 导入后目录状态，使用模拟数据。04 ZIP 和实际 CSV 没有导入店铺。不要把这些证据说成本次新店已经导入、真实商品、登录或支付验证；每次生成后仍执行本次检查。若骨架不可用，可按下文自行实现原生功能并明确实际验证范围，不回退官方主题。

## 参考站与已核实摘记

每次优先查看用户最新参考的可访问页面，能看桌面 / 手机图像时查看实际排版。网页文本只能证明结构与内容，不能据此声称确认了像素、字体、颜色、动画或移动裁切。不要无限重试同一网络故障。

以下摘记来自 2026-10-26 的实际读取，不是永久不变的规范：

- **Kicks Europe**：首页可读取到公告、简洁分类导航、主视觉与集合入口、分类索引、精选商品区，商品提供直接加入与选择选项两类入口；页脚含联系表单，以及服务和政策链接分组，还能看到搜索与空购物车入口。当前页面展示眼镜，因此本次做鞋履时只参考结构，商品与场景改为鞋履。[来源：首页](https://kickseurope.store/)
- **Rawtrees**：首页在本次网页读取和浏览器中连接失败；可读取到其联系页的分类导航、联系与订单帮助、政策和客服分组、搜索及空购物车结构。用户另提供的页脚截图为双列链接示例。未确认首页视觉细节，不声称复制出其原主题。[来源：联系页](https://www.rawtrees.com/pages/contact-us)

可借鉴的设计取舍是清楚的分类入口、明确的主视觉、商品优先、购买与选择选项的区分、容易找到的客服与政策。将这些取舍转化为本店独立设计；仅参考布局时不移植商品目录或图片。用户明确要求抓取商品、分类与图片时，按 [source-catalog.md](source-catalog.md) 使用核对过的商品事实与真实媒体；这不授权移植其店主身份、公司资料、支付方式、退换承诺、政策正文或应用。参考网页不能恢复完整 Liquid / schema 主题源码。

新增的 Ksubi、JOOLA、Cotopaxi 结构观察、读取范围与设计推演见 [reference-layout-library.md](reference-layout-library.md)。这些是设计原则来源，不是三个固定母版。

上述观察之外的视觉方向属于本次自主设计：按品类确定构图、字级、间距、配色比例与细节。遵守 design-and-content 中的内容职责、审美边界和精致度要求，首页顺序与展示形式自由决定；目录抓取遵循本次明确范围，不把源站促销套成店主优惠。

## 自主编写完整原生主题

至少建立八个交付根目录：assets、blocks、config、layout、locales、sections、snippets、templates，按原生 Shopify Liquid / JSON 架构实现，而非只写一页静态 HTML。

- **基础与编辑器**：layout/theme.liquid、content_for_header、content_for_layout、有效 settings_schema / settings_data、颜色方案定义 / 实例 / role / CSS、翻译资源、可编辑的 Header / Footer section groups、首页 JSON 与可重加的 section presets、必要的 app 扩展接入。主题名称说明为本次自建设计，不冒充参考站原版或官方主题。
- **商品与集合**：实际 product、collection、list-collections 模板，真实商品 / 价格 / 图片 / 可售状态，商品变体选择、正确表单 ID、数量、售罄处理、集合分页和适用的排序 / 筛选。快速购买对多变体先选项，不购买错误变体；商品不足不造样品。
- **购物车与结账入口**：原生 cart 模板 / 表单、更新数量 / 删除、正确折扣及价格呈现，结账提交到 Shopify。若有抽屉增强，使用原生 Cart API 和本地化路由，保留可用的普通购物车退路；不能把本地数组当真实购物车。
- **搜索与账户**：可用的原生 search 模板 / 搜索表单 / 分页，搜索或账户不能只是图标。账户链接按 Shopify routes / 店铺启用方式处理，不伪造登录、注册或身份系统；有旧账户需求时提供其所需 customer 模板，不擅自更改账户模式。
- **其他页面**：普通 page、contact 表单、404、密码页及本次需要的 blog / article、gift card 等模板。不能为省事把商品页、集合页、政策页或搜索结果都重定向到首页。
- **本地化与原生能力**：按真实配置提供语言、国家 / 货币 localization form，使用 routes 与 Shopify money 处理，保留应用、原生支付按钮和系统入口的可接入性。不触碰后台支付、订单或结账配置。

查当前官方开发文档核对接口和 schema，例如 [主题架构](https://shopify.dev/docs/storefronts/themes/architecture)、[Liquid 表单](https://shopify.dev/docs/api/liquid/tags/form)、[routes](https://shopify.dev/docs/api/liquid/objects/routes)、[Cart API](https://shopify.dev/docs/api/ajax/reference/cart)。这是开发规范来源，不是主题底座。

自主编写后仍按 validation-and-delivery 执行真实校验；缺少店铺数据时可以完成源码与 ZIP，但不能声称已验证真实商品调用、账户登录或线上购物车。不能因当前无店铺而删掉这些功能。

## 工作目录与结果

当前工作区的 `output/shopify` 可作为默认根位置，无须其中预先存在模板。为每次任务建立独立工作目录，原生主题文件放其中的 theme 子目录，设计 / 检查记录也留在工作目录。最终成品另放“品牌或参考站简称(品类)”文件夹，例如 `output/shopify/psychobunny(服装)`；用户指定其他名称／目录时保持其要求。涉及商品抓取默认仅主题 ZIP 与一份 CSV；指定多份目录时保留指定 CSV 份数，详见 validation-and-delivery。政策正文和当前页面内容清单保存在主题内，外部草稿仅为附加材料；不覆盖无关成品。

最终交付可上传主题 ZIP；涉及抓取商品/分类时，同时独立交付商品 CSV，默认仅这两份安装文件，不再生成全量素材整合 ZIP。具体边界见 [validation-and-delivery.md](validation-and-delivery.md)。修改本技能的请求只修改技能；执行装修命令时才按本流程持续实施至交付。
