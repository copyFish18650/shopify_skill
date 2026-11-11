# EstateKid：基础站整站观察

记录日期：2026-11-03。用户将 [EstateKid](https://estatekid.com/) 定义为“基础站”的默认高复刻参考，实施要求见 [基础站标准](basic-store-standard.md)。这是参考研究与视觉证据，不是原主题源码、可上传主题或已完成的新店。精品站另用 Cozyster，不把两站组件合成固定母版。

## 证据层级

- 公开 HTTP：23 份 HTML／CSS／JS 来源均返回 200。覆盖首页、3 个集合、集合总览、鞋与 T 恤详情、搜索、空购物车、About／Contact／Payment、6 个政策及 sitemap；资源含 `en-store.css`、`en-store.js` 和原生样式。平台可由公开 Shopify CDN、脚本及原生产品／集合／购物车结构确认。公开页面不能恢复完整 Liquid、section schema、Theme Editor 配置或后台库存。
- 浏览器实际观察：1280×720 桌面首页、鞋类集合和鞋 PDP 首屏；390×844 请求视口下的手机首页、PDP、菜单展开及关闭。移动截图导出栅格为 380×822，不能直接把截图像素作为 390px CSS 测量。首页标题等桌面值另以只读 computed style 核对。
- 尚未实测：下半整页视觉、hover／完整图库切换、筛选及排序提交、规格与吸底栏联动、非空购物车、异步推荐、联系投递及结账。下述相关行为若来自源码，会明确标注，不将其说成点击通过。一次 fullPage 截图请求只返回首屏，未取得整页截图。

研究快照、逐 URL 状态、字节和 SHA256 留在本次工作目录。随技能保留的六张参考截图位于 `assets/reference-screenshots/estatekid/`，仅用于学习、对照，不放进生成主题 ZIP，也不当作可直接使用的店铺素材。

| 画面 | 参考截图 |
| --- | --- |
| 桌面首页首屏 | [1280×720](../assets/reference-screenshots/estatekid/home-desktop-1280.jpg) |
| 桌面集合首屏 | [1280×720](../assets/reference-screenshots/estatekid/collection-desktop-1280.jpg) |
| 桌面详情首屏 | [1280×720](../assets/reference-screenshots/estatekid/product-desktop-1280.jpg) |
| 手机首页首屏 | [390px 请求视口](../assets/reference-screenshots/estatekid/home-mobile-390.jpg) |
| 手机详情首屏 | [390px 请求视口](../assets/reference-screenshots/estatekid/product-mobile-390.jpg) |
| 手机菜单展开 | [390px 请求视口](../assets/reference-screenshots/estatekid/menu-mobile-390.jpg) |

## 首页、导航与内容节奏

[首页](https://estatekid.com/) 实际 MainContent 顺序是：全幅影像 Hero → 4 张 Collections → 4 张 Now trending 商品 → 4 张 Shop Our Icons 商品 → 6 张生活／运动图库。后接全站 Footer。五段内容各有清楚职责，不是通用 Hero → 服务条 → 商品 → Lifestyle → FAQ 骨架，也不是大量装饰模块。

已看见的首屏为黑色公告条、覆盖在大幅滑板场景上的白色圆角导航、大号窄体粗标题、短句、蓝／白双 CTA 和右下播放控件。桌面导航显示 9 个平铺品类及搜索、US、账户、购物车。手机改为左菜单、中偏左 Logo、右搜索与购物车，白色菜单面板在导航下展开，纵向显示同一组分类；开、关已操作确认。

首页源码中的 Hero 有海报及桌面／手机 MP4 数据源，主 CTA 去真实商品集合，视频 CTA 去 YouTube。实际首屏可见影像与播放控件，但本次未按播放键测试音视频全流程。适配其他品类时换成相应可用影像、商品与文案；没有合适视频不能留下空播放按钮或复制与本店无关的滑板联名。

分类为正方形图卡，标题与箭头在图下。两个商品区同为方图、窄体产品名和简短品类说明，但选品不同。生活图库有前后箭头。未发现首页 FAQ、评论、Newsletter、信任条、长品牌宣言；不为凑复杂度加入，本站已有服务职责另确保可达。没有实际社交账户或用户授权素材时，图库可保留布局并改为本店生活影像，不虚称 Instagram 社区或 UGC。

原首页 8 张自定义商品卡**没有价格、划线价或快速加购**。这是已确认的本站必要适配：保留真实售价、有依据的划线原价与正确购买／选项路径，不能借高复刻省掉用户要求的商品信息。

## 两套商品卡片

首页卡片与内页卡片不是同一个组件：

| 场景 | 观察到的结构 | 交互证据与待验 |
| --- | --- | --- |
| 首页两组商品 | 方图、主副图、窄体粗标题、灰色品类说明，源站缺价格 | CSS 为 hover／focus 250ms 淡化副图；手机禁用 hover 副图并横滑。源码确认，未做本次 hover／横滑操作。 |
| 集合／搜索／空车推荐 | 原生 product-card，媒体轮播、Sale、Choose、标题、现价及有效划线价 | 桌面集合实际看见四列与双价；源码有 Previous／Next、quick-add 事件和真实商品链接，未打开 Choose 流程。 |

复刻时分别还原两套视觉密度和控件层级，不把首页卡复制进全部列表，也不把只有事件钩子当作快捷购买已实现。副图、轮播、规格使用本站真实数据；单图、缺图、售罄与失败状态保留稳定回退。首页补双价时以原卡片字级和紧凑节奏适配，不挤坏标题或手机轨道。

## 分类、搜索与集合总览

[鞋类集合](https://estatekid.com/collections/skate-shoes) 分为大标题区与商品结果区。实际桌面首屏：左侧 Availability／Price，右侧带说明的数量、Sort 和两种网格图标；下方是干净白底商品图、简洁标题及双价，没有裸 ID 数字或原生粗糙表单堆叠。

源码确认 Shopify Availability／Price 参数、活动筛选与 Clear、`sort_by`、列数切换、手机 facets drawer，商品区存在 infinite-scroll 钩子。抓取时鞋类 178 商品、首批 24；[T 恤](https://estatekid.com/collections/t-shirts) 28、首批 24；[Best Sellers](https://estatekid.com/collections/best-sellers) 15。这些是历史源站数据，不能硬编码为新站数量。未触发加载下一页或筛选／排序结果，未来制作需实际核对。

桌面 medium 卡宽在源码使用 `repeat(auto-fill,minmax(250px,1fr))`，本次 1280px 画面为四列；手机集合为两列。首页手机是横滑卡轨，不要误写为所有场景固定 4／2 网格。

[搜索结果](https://estatekid.com/search?q=shoe&type=product) 复用商品卡与过滤／排序，读取时有 184 个结果、首批 24；无结果和预测搜索操作仍待验。Header 预测搜索的 dialog／combobox、清除与键盘事件来自源码，不证明已实测。

[集合总览](https://estatekid.com/collections) 有 13 个分类卡，含一个名为 Home page 的源站集合。新站按本站商品／Type／集合组织，剔除无意义内部分类；真实分类自动接入 Header，不移植这 13 个分类或 9 个导航名称。

## 商品详情与购买

读取 [鞋样本](https://estatekid.com/products/locut-x-andy-anderson-white-green-4107000638-167) 与 [T 恤样本](https://estatekid.com/products/3-pines-tee-black-4130004078-001)。两者均有图库、产品标题／价格、颜色、尺码 radio、数量、原生 Add to cart、描述／属性、放大与推荐容器。

桌面鞋 PDP 实际看见左侧双列大图、右侧产品信息与尺码矩阵，信息栏约占三分之一宽度；媒体有产品、场景和细节的混合。手机实际看见单幅大媒体、分页圆点，随后标题、价格、颜色和尺码矩阵；不是将桌面双列 21 张图片缩成狭窄长墙。

源码鞋样本有 21 媒体／21 尺码；T 恤有 2 媒体／S–XXL 五尺码。规格与数量表单走 Shopify 原生 `/cart/add`。页面含 Quick add to cart bar／`sticky-add-to-cart`，应按当前商品选项、双价、库存和数量同步，但本次未滚动触发与购买测试。推荐源为原生 related intent／limit=4，浏览器与初始 HTML 只见加载容器，不能称已显示四个真实推荐，也不能填示例商品冒充。

不同产品的原站折扣不一致，鞋样本为单价，T 恤有双价。本站按已确认 [逐站优惠与双价规则](pricing-and-promotions.md) 处理真实依据，不套源站折扣或二次打折。商品名称、材质、鞋码、颜色、规格和养护都从本次目录读取。

## 购物车、服务与 Footer

[空购物车](https://estatekid.com/cart) 源码有继续购物、账户入口和四张真实商品导购；全站有原生空车 drawer。未测试非空车、改数量、删除或结账，不能从空态推断整条购买路径通过。

Footer 的实际源码为黑底白字：联系资料、Customer Service、Our Policies 与版权／工具行。服务入口包括 Search、外部 17track、[About](https://estatekid.com/pages/about-us)、[Payment](https://estatekid.com/pages/payment-terms)、[Contact](https://estatekid.com/pages/contact-us)；政策为独立 `/policies/contact-information`、`legal-notice`、`privacy-policy`、`refund-policy`、`shipping-policy`、`terms-of-service`。不是政策弹窗。本次服务／Footer 仅源码核对，没有声称整页视觉已看过。

重要适配：源站 Contact 是文本联系页，不是原生联系表单；Header 的 US 是静态 span，不是国家／货币控件；Footer 没有语言／货币表单、Newsletter 或支付图标。本站仍保留原生联系表单、真实语言／国家与对应货币、已确认的适用服务职责，去掉重复目的地和空栏目，Reviews／Newsletter 默认关闭。外部 17track 链接不等于订单系统已集成。主题包不能自动创建后台 Pages，缺页面要保留明确待配置状态，按 [Footer 与政策](footer-and-policies.md) 落实。

政策可学习信息组织：About 的经营与购物说明，Contact 的订单咨询／退货指引，Payment 的结账金额与授权／退款，Privacy 的信息与用途／服务商／权利，Shipping 的费用／处理／运输／延迟，Refund 的条件／流程／费用，Terms／Legal 的合同与主体披露。**不得移植源站姓名、地址、邮箱电话、Logo、域名、品牌故事、更新日期、像素／隐私设置或配送退款时效。** 本店已确认的政策底稿优先，尤其 30 天收货退货、免费退运、无补货费和未履约 15 分钟取消。地址不自动成为仓库或退货接收地点。

## 可复用的尺寸与响应式记录

以下为 2026-11-03 源站 CSS／computed style 观察值，用于高还原对照，不是自主模式通用模板或固定断言。

| 区域 | 数值／组织 |
| --- | --- |
| 首页字体 | `EN Sans` 400／500／700；`EN Condensed` 900。computed style 的首页 H1 为 48px／900，section H2 为 26px／900，产品 H3 为 19px／900。原生内页为 Lato 系列。源字体文件涉及 HelveticaNeueLTPro，不能假定有权随包分发；用可用字体比较字宽、字重、行高和断行并记录替代。 |
| 颜色 | 首页内容底 #f3f3f5，文本 #111，蓝按钮 #244b9c／hover #0f266a，次文 #697389，白图卡，黑 Footer。 |
| 容器 | max-width 1504px，桌面两侧 32px；≤1199 为 24px，≤749 为 16px。 |
| 公告／导航 | 公告 34px／移动 32；导航左右 16、顶部 16、圆角 16、主行 74px；手机左右 10、顶部 12、圆角 12、主行 62px。≤989 切换手机导航，≤1199 隐藏静态 US 并压缩间距。 |
| Hero | 70vh／min600px；手机 72vh／min570px。cover 媒体、可读阴影叠层，文字底距 32／24px；标题 48／38px，正文 16／14px。 |
| CTA | 桌面 min-height56、padding16／32、radius8；手机高48、padding14／18。 |
| 首页布局 | 桌面四列、gap16，上下 section 间距 32；手机 section 间距 24。分类和产品图 1:1、radius14，分类标题 24／22，产品标题 19／20。 |
| 手机首页轨道 | ≤749 分类／商品 `grid-auto-flow:column`，卡宽77%、gap14、scroll-snap。图库六列→≤989 三列→≤749 卡宽55%。 |
| PDP 媒体与信息 | 两列媒体、媒体 gap4／radius0，缩略图44；信息区 gap48，sidebar25rem，核心列 `1fr min(50vw,var(--sidebar-width))`。 |
| 源码交互 | 副图 opacity250ms；分类 hover brightness .92；按钮背景200ms；图库按轨道宽75%滚动。减少动态效果时停默认视频并清除动画／过渡；离屏视频暂停。 |

源码还见 Escape 关闭、details 互斥、外点关闭、搜索打开聚焦、Theme Editor 重载清理。`.en-mega`、film、newsletter 等通用组件 CSS／JS 不代表实际首页存在对应实例；平铺菜单不要写成已验证 Mega Menu。

## 后续复刻如何使用

先重新观察当前参考，再用相同视口比较输出。模块顺序、密度、图片比例、裁切、字级、卡片和响应式按本参考；已确认的真实数据、双价、本站政策、原生功能与可编辑性保留。必要适配逐项说明，参考未见状态补验后再称还原完成。

本次已经更新的是学习资料、模式路由与创建／验收要求；`prepare_theme.py` 仍是功能底稿准备器，不能因为它的提示文字更新就声称自动生成 EstateKid 展示层。历史 ZIP、CSV 和线上店铺本次未修改。
