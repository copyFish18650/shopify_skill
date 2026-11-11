# 页脚、条款与品类

后续用户已要求按品类自动修改页脚条款，取代早期“不要自动创建政策”的限制。借鉴信息组织，正文以本店真实经营为依据，不能复制参考站后只换店名。

2026-10-28 用户进一步明确采用参考站的通用经营规则，并以自己的后台截图覆盖冲突值。先执行 [merchant-policy-defaults.md](merchant-policy-defaults.md)，使用 [merchant-policy-defaults.json](../assets/merchant-policy-defaults.json) 的完整正文与确认事实；不要再把这些条件当成未知承诺。主体、隐私实践和法域不随参考站移植。

最新默认是个人经营、本次姓名和证件地址、站内联系表单；公开联系地址按本站本次资料填写，不自动把账户邮箱当客服邮箱。用户明确确认本次公开客服邮箱时可在本站联系栏显示，具体地址不进入共享技能。不用历史样例姓名替换每个店；不把资料包的登录邮箱、密码或不明编号猜作客服资料。遵守这些公开范围，同时如实保留实际隐私配置及必要法律披露的核对项。

## 精品严格复刻的可见 Footer

精品高复刻的可见栏目、标题、链接数量与顺序、列布局、字号间距和默认开关，以本次参考截图及最新明确指示为准。它们优先于旧骨架的 Customer Service／Customer Care 两组、14 项可见文档和 Newsletter 默认关闭。完整政策职责与 Footer 可见清单分别验收；不能以“正文更完整”为由擅自多加入口。

本次用户要求严格同步 Cozyster 图2，四列由左至右为：

| 列 | 本次可见内容与顺序 |
| --- | --- |
| Contact Information | 本站已确认且允许公开的联系资料；它是资料列，不另加同名政策链接，不复制参考站姓名、邮箱、地址或经营承诺。 |
| Customer Service | Search → About Us → Contact Us → Order Tracking → Size Chart。 |
| Our Policies | Privacy Policy → Refund Policy → Shipping Policy → Terms of Service → Payment Terms & Billing Policy。 |
| Newsletter Sign Up | 开启真实 Shopify 原生订阅表单，还原本次截图的标题、说明和控件；保留真实提交、成功／错误反馈，不伪造订阅成功。 |

这次是两组各五个菜单链接，共十个；Contact Information 资料和 Newsletter 表单不计作额外菜单链接。名称按截图，不擅自把 Refund Policy 改为 Return & Refund Policy、Size Chart 改为 Product Guide，或把 Payment Terms & Billing Policy 缩成旧标题。不得自动追加 After-sales Support、Your Privacy Choices、Contact Information 链接、Legal Notice、Terms of Sale 或其他截图外入口。

未摆在 Footer 的必要政策／服务正文仍保留在主题可编辑草稿、保存配置或归档中；已有后台政策／Pages 不因收紧 Footer 而删除。隐藏归档不代表经营规则或法律披露已被取消，也不代表后台内容已经更新。新增参考或新截图时重新按其真实 Footer 列表和开关实施，不把本次四列／十项固化为所有精品站的通用数量。基础与自主模式继续原规则。

严格复刻不授权猜造未知 URL。Search 用原生路由；其余入口解析实际已发布 Page／非空原生 Policy 或本次已确认的有效目的地。缺资源保留相应标题的明确非交互待配置状态，不拼接假 handle、不加政策弹窗，也不把十个标题称为十个已经上线的页面。原生本地化、适用 app／支付能力按既有要求保留并与截图布局协调，不用增加政策链接来补功能。

## 底部支付图标区：所有模式默认开启

用户新增的跨模式要求：基础站、精品站、自主设计及后续批量站，都在 Footer 底部保留默认开启的支付品牌图标区。参考 Cozyster 截图中底部分隔线、左侧版权、右侧原彩支付图标横排；在原生语言／国家货币控件共存时合理分行，手机允许换行，不压缩拉伸、溢出或重复放两组图标。Footer 上方的列数／政策清单仍按本次模式，不因新增支付行统一成四列。

- 保留 Theme Editor 的 `show_payments` 兼容 ID（或原主题等价开关），schema default、preset 及保存的 footer-group 默认都为 true；用户明确关闭某站时保留其例外。有原主题不为此重置其他设置。
- 默认遍历 `shop.enabled_payment_types`，用 `payment_type_svg_tag` 输出官方 SVG；显示实际配置返回的类型，保留原彩、比例及可访问名称，不画仿制标识、不复制参考站图片条，也不额外请求第三方图标脚本。截图中的 Visa、Mastercard、American Express、Apple Pay、Diners Club、Discover、PayPal、Google Pay、Shop Pay 是参考布局，不代表新店都已开通。
- 图标大小按本次 Footer 比例调整，桌面可参考约 48×30px、间距 8px；手机用约 44px 宽并自然换行。具体可随模式适配，不能把很小、被 CSS 隐藏或全灰的图标当作达到了参考效果。
- 本地验证覆盖空、单个和多个支付选项；用于看图的模拟数据必须明确是工作目录里的私有预览夹具，不写进交付主题冒充真实开通方式。空数组时检查开关和后台前提，不能凭空增加支付品牌。实店有条件时再核对前台图标与实际付款配置。
- 手动操作入口：Shopify 后台 **在线商店 → 主题 → 对应主题的编辑主题／自定义 → Footer（页脚）→ Show actual payment icons／Show payment icons → 保存**。开关已开启仍没有图标时，再到 **设置 → Payments（付款）** 核对已激活、配置完成的支付提供商；具体图标由 Shopify 返回的数据决定。展示图标不会开通 Shopify Payments、钱包或第三方付款方式，不自动改动这些系统。

官方依据：[主题支付图标排查](https://help.shopify.com/en/manual/online-store/themes/theme-support/troubleshooting)、[shop.enabled_payment_types](https://shopify.dev/docs/api/liquid/objects/shop#shop-enabled_payment_types)、[payment_type_svg_tag](https://shopify.dev/docs/api/liquid/filters/payment_type_svg_tag)。2026-11-03 核对；未来操作仍查当前平台界面。

## 参照站完整度的验收目标

用户要求政策完整时，逐项核对联系信息、退换退款、配送、服务条款、法律声明、隐私、联系我们、关于我们、订单追踪等适用正文职责及指南、付款、售后帮助。这里是内容覆盖要求，不是要求把九项或十四项全列在 Footer；精品严格复刻按上节的可见清单实施。以完整信息、有效入口、页面可读性和规则一致性验收，不能用模块数、字数或静态检查替代正文审阅。

Footer 服务与政策默认都走普通链接，打开实际独立页面，不用阅读弹窗、fragment 或查询参数伪装页面。实店验收须逐页验证实际政策／帮助资源和 Footer 链接，核对适用的结账政策关联与联系路径。独立 URL 有助于正常抓取，但不保证谷歌收录；还取决于页面发布、密码／索引设置等。姓名与联系地址仅取本站绑定资料，不能因此伪造完整法律披露。目标店及后台操作范围未明确时只引导必要补充，不猜用历史店铺。

早期截图曾含 Legal Notice、Contact Information 链接等更多项目，仅作历史结构资料；本次 Cozyster 图2的严格可见清单以本节前述最新要求为准，不从旧截图补回额外入口。

## 事实与适配

先读本次提供或有权访问的现有政策、页面、菜单、店铺资料和商品。核对主体 / 联系方式、目的地、处理 / 配送时效、运费 / 免邮、退换期限 / 条件 / 费用 / 地址、损坏 / 错发、取消、实际支付说明、跟踪入口和真实尺寸。

用户最新明确指示与真实后台数据优先；有冲突时指出具体冲突，不私自覆盖经营条件。按品类自动调整商品术语、结构、相关栏目和有依据的正文。不能从品类推断退货期限、最终销售、卫生限制、费用、保修、税费、配送承诺或法律适用。

| 栏目 | 处理原则 |
| --- | --- |
| Privacy Policy | 复用现有政策。数据、Cookie、跟踪应用和地区权利取决于真实配置，不能仅换品类就猜测改写。 |
| Refund / Return Policy | 统一商品术语，核对尺码、试穿 / 使用、配件 / 包装的真实规则；保留确认的期限、费用和流程，不自行增加不退条件。 |
| Shipping Policy | 使用实际处理、配送、费用、地区、追踪资料；大件或特殊包装等说明须有依据。 |
| Terms of Service / Terms of Sale | 保留真实主体、市场和购买条件，必要时改准确的商品描述，不照抄他站管辖地、免责或品牌信息。 |
| Payment Terms | 只描述实际支付方式、币种与已确认收费，不改支付网关、配置和结账。 |
| Legal Notice / Contact Information | 使用本次真实主体及允许公开的联系渠道；按本次证件填写公开联系地址，不使用账户邮箱作客服邮箱。必要法律披露另核对，不伪造电话、注册资料或法域。 |
| About Us | 基于实际品牌 / 商品定位，不虚构年份、团队、产地、工厂或认证。 |
| Contact Us | 复用有效联系页或原生 contact form，使用确认的联系方式。 |
| Order Tracking | 使用真实跟踪页 / 应用 / Shopify 订单入口；没有时准备有依据的帮助草稿，不能冒充已接入系统。 |
| Search | 保留 Shopify 真实搜索路由与功能。 |
| Size / Dimensions / Care Guide | 按下表及实际商品资料选择，不给所有品类套服装尺码表。 |

| 品类 | 指南和核对重点 |
| --- | --- |
| 服装 | Size Guide、量体方式、真实尺码 / 成分 / 养护；按实际目录区分成人、童装、大码/加长及鞋履配件，不共用一张无依据的通用换算表；确认试穿、标签和换码规则。 |
| 鞋履 | Shoe Size Guide、真实 US / UK / EU / CM 数据、量脚说明及款式差异；无依据不编换算、楦型或正码结论。 |
| 包袋 | Dimensions / Product Details / Care Guide；真实长宽高、容量、肩带、材质；不强塞服装尺码，不虚构真皮、防水或电脑尺寸适配。 |
| 家居 | 尺寸、容量、使用 / 养护；食品接触、耐温、洗碗机兼容等须有真实依据。 |
| 运动器材 / 匹克球 | Equipment / Specifications / Care Guide；核对具体型号的尺寸、重量、握把、配件兼容与保养，不推测性能、比赛批准、认证或保修。 |
| 混合品类 | 总的 Product Guides 入口可按品类分组，商品页指向准确指南，不能共用错误尺码表。 |

## 主题与后台边界

Policy 正文、普通 Pages 和菜单由 Shopify 后台管理，ZIP 中添加 page template 或硬编码 `/policies/...` 不会自动创建它们。页脚使用可配置 link_list、有效 page 设置和真实非空 shop.policies，保留 Theme Editor 展示配置；有原主题时优先复用其组件。自主构建同样不能硬编码假菜单、假 handle 或未经确认存在的政策链接。

- 有真实资料、当前任务授权后台修改且工具支持时，在授权范围保存政策 / Pages / 页脚菜单，然后重新读取核对。不改顶部导航、支付、订单和结账配置。
- 只有主题文件时，仍保留完整服务／政策的可编辑草稿，包括本次不显示的必要归档文档，并提供 `templates/page.service.json`、对应 section、阅读样式和 `assets/service-pages-manifest.json` 内容清单。清单从本次最终保存的 Footer 草稿 blocks 生成，包含标题、文档类型、建议 handle、正文与来源哈希；草稿存在不要求自动输出一个 Footer 链接。不把旧项目身份、绝对路径或源 ZIP 哈希冒充当前成品。它便于后续创建真实 Pages，不会自行创建资源。
- 链接解析顺序为：店主指定且已发布的 Page → 开启优先时正文和 URL 均非空的原生 Policy → 实际存在且已发布的对应 Page／已确认别名。未来定时发布、隐藏或不存在的页面不生成链接。缺资源时输出明确非交互待配置文字，并仅在编辑器显示设置提示；不跳 404、不回退弹窗、不把空入口称为完整上线。获取目标店和已授权后台范围后，创建／绑定缺失 Pages，再重新读取验证；本地交付中如实说明未完成的后台配置。
- 缺关键事实时先应用确认底稿并填写本次姓名与证件地址；姓名缺失或地址有缺项才标记 #待填入。地址在 Footer 可编辑设置 operator_address 维护，Footer 与内置 Contact Information / Legal Notice 共用，避免手工重复粘贴。不自动公开账户邮箱，不留空邮箱栏；内置 Contact Information 正文可引用真实站内联系表单，本次资料列不因此另做同名菜单链接。实际隐私配置与必要法律披露集中在对应文档，其他正文引用。退货目的地可在批准指引中提供。交付时列最少缺项，不反复索要已确认时效、费用或可省略的品牌故事。
- 保留已有有效政策资源及适用阅读入口；精品严格截图之外的链接不要求继续在 Footer 可见，可保留后台／归档。隐藏空栏目只是视觉处理，不能因此声称政策完整；缺少的必要资料在交付中列明。

## 已验证的内置文档结构

自编骨架采用 `layout/theme.liquid` 中的 `{% sections 'footer-group' %}`、`sections/footer-group.json` 和 `sections/footer.liquid`。文档正文同时放在 Footer 的 block schema/presets 及 group 保存配置中，使初次导入和删除后重新添加 Footer 都有正文。保持所有引用、block types、block_order 和设置 ID 一致。

- 旧功能底稿提供 Customer Service / Customer Care 两组及十四份草稿：About Us、Payment Terms、品类指南、Order Tracking、Contact Us、Your Privacy Choices，以及 Privacy Policy、Return & Refund Policy、Shipping Policy、After-sales Support、Terms of Service、Contact Information、Legal Notice、Terms of Sale。它们是可复用的内容资产，不是精品严格复刻的可见菜单清单；按本次参考挑选可见入口，其余必要正文隐藏归档。
- 这不是固定双列深色页脚。精品严格复刻的分组、标题、列数、开关、颜色、字号与留白按本次参考；基础／自主模式沿用各自规则，保留适用正文和编辑能力。
- 一个 section 或 block 的 settings 数组中只放一个 `link_list`。额外菜单用可重复的 Navigation menu blocks，每个块一个选择器；没有实际链接时不输出栏目。这是实际 Shopify 保存曾拒绝的约束，Theme Check 当时没有拦截。
- 正文用可编辑 `richtext` 保存在主题内；独立 Page 用原生 `page.content` 渲染，页面标题、正文、移动行长与深浅色方案都应清楚。Contact Us 使用实际 contact Page／原生表单，不伪造联系方式或跟踪系统。菜单和文档链接无 JavaScript 也应正常跳转，不由脚本拦截打开政策 dialog。
- 保留真实 page 覆盖和“优先使用已发布店铺政策”。支持 privacy → `shop.privacy_policy`、returns → `shop.refund_policy`、shipping → `shop.shipping_policy`、terms → `shop.terms_of_service`，并核对其他可用原生政策。仅当正文及 URL 非空时采用；否则查实际 Page，不直接拼接 `/policies/...`。

## 去重与原生本地化

- 核对整块 Footer 的真实目的地，包含主菜单、菜单 blocks、Page blocks、服务／政策组和左侧快捷入口。Contact Us、品类指南已在文档组出现时，去掉重复快捷项；同一 URL 只保留适当入口。基础／自主模式保留适用的独有帮助链接；精品严格复刻仅在本次参考可见清单内保留独有入口，不因 URL 不同而额外加链接。去重后没有链接或有效内容的栏目不输出，不删除政策正文、地址、Newsletter 开关、app 或原生支付图标来凑简洁。
- Footer 提供可在编辑器关闭的语言和国家／对应货币控件，默认开启。使用 `{% form 'localization' %}`，从 `localization.available_countries`／`available_languages` 读取真实选项；提交 `country_code`／`language_code`，当前值来自 `localization.country`／`language`。国家标签可含货币 ISO 与符号，不虚构独立 `currency_code` 选择器或前端换汇。
- 只有一个可用选项时显示当前值；多于一个才显示对应 select。仅一项可变时保留另一当前代码，避免误切换。Header、Footer 和多个 section 实例使用含 `section.id` 的不同表单／label ID；保留原生提交按钮与无 JS 路径，不靠自动触发脚本才可用。
- 控件沿用本站颜色、字体与焦点样式；手机 select 至少 16px、操作目标至少 44px，长国家名和大量选项不能撑破布局。检查 320px、常用手机和桌面，控件与按钮在 Footer 边界内且可点击。后台需真实启用语言／Markets 对应币种，主题 ZIP 不能替店铺启用它们或更改支付配置。

## 店主后续编辑的同步范围

在主题编辑器 → Footer → Contact address 修改共享地址，保存后 Footer 的内置地址展示更新；主题内联系／法律草稿可以共用该设置，但已创建的 Page 正文是单独保存的内容，不会自动改地址。Footer → Policy document 是包内草稿；修改后须刷新内容清单，并在已获授权的后台另行更新相应 Page，不能声称编辑 block 会双向同步 Pages。Page 页面正文在 Shopify Pages 中维护；优先使用的原生政策在“设置 → 政策”中维护，保存后链接读取该资源的最新正文，不回写 block。Shopify 上的修改也不会自动改变本地 ZIP。重复时效仍须保持一致，除非本次实际实现并验证共享字段。

存在 Shopify 自动维护政策时保留其配置，不为改文案擅自切换自动维护开关。不能承诺主题 ZIP 会修改结账页政策。涉及具体法律结论时查当前权威来源，不声称自动适配保证合法合规。

使用时检查最新官方说明：[Shopify 店铺政策维护](https://help.shopify.com/en/manual/checkout-settings/refund-privacy-tos)、[创建、编辑与发布 Pages](https://help.shopify.com/en/manual/online-store/add-edit-pages)、[菜单说明](https://help.shopify.com/en/manual/online-store/menus-and-links/understanding-navigation)、[原生语言与国家控件](https://shopify.dev/docs/storefronts/themes/markets/multiple-currencies-languages)。
