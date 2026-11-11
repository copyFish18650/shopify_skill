# 本地 CSS 与零售微交互知识库

各模式从此库选择适合本站购物任务的反馈，并按 [站间差异规范](site-diversity.md) 实施。精品优先保留用户认可的成熟样式与可靠交互，只做少量适配；基础与自主模式按各自方向协调变化。不机械套用本库示例尺寸／时长，也不为差异堆砌动画；技术与可用性边界继续适用。

这是设计时读取的本地知识资源，不是线上特效库、CDN 或外部数据库连接。结合真实商品、当前版式与近期成品选择组合；每次生成时确定行为，顾客访问时不随机更换导航、按钮或动效。这里是组件手法，不是若干套固定整站模板。

## 选择组合

用户要求小交互丰富、正式、高级且每站有特点。优先覆盖本次存在的主要流程：顶部导航、分类浏览、商品媒体/选项/购买、内容披露、购物车和客服。区别应来自信息呈现与操作反馈，不止颜色、照片和过渡时长。以有用的状态反馈为主，装饰次之；不要为数量让每个模块都弹跳、浮起、自动轮播或滚动入场。

先给本店确定一套节奏与材料感，再为主组件选择差异。例如目录型可以用编号/边线和真实规格披露；摄影陈列可用辅图、克制裁切与快捷查看；编辑式商店可用文字索引、分类预览和细分下划线。可以混合，不按固定轮换或风格代号套版。

在 design.json 记录：重要模块采用什么、数据来自哪里、鼠标/键盘/触控怎么操作、无增强 JS/减少动态效果的回退，以及相对近期作品的区别。不要用“随机高级动画”代替具体实现。

## 可组合的 CSS 模式

| 模块 | 模式与实现要点 | 适用条件 / 回退 |
| --- | --- | --- |
| 导航链接 | `::after` + `scaleX` 形成生长下划线、上沿线或当前项指示；改变 `transform-origin` 调整阅读方向 | 焦点与 `aria-current` 同样清楚；装饰不改变链接尺寸 |
| 分类主导航 | 原生链接配细框、柔和底色或短箭头；宽屏横排，必要时合理换行；手机紧凑横向捷径 + 完整菜单 | 读取真实集合/Type/确认映射；不能只有空后台菜单、不能按标题猜分类 |
| 多级菜单 | 原生 `details/summary`，鼠标意图延迟约一瞬再展开，离开后短延迟关闭 | 点击和键盘独立可用；Escape/外部点击关闭、焦点恢复；不用 hover-only 菜单 |
| 搜索 | 展开后焦点进入搜索输入，边线/背景反馈提示当前编辑区域 | 保留原生 GET/q/本地化路由；关闭回到触发器，不制造模拟结果 |
| 主按钮 | 小距离图标平移、内嵌底色/细框、按下与等待反馈 | 不用 `transition: all`；不动态改变宽高，不移动主要文案 |
| 文本与页脚链接 | 细下划线、字色或边线反馈 | 手机始终像链接，不能把唯一可点击入口隐藏到 hover |
| 分类图卡 | 极小幅度缩放、上移或边缘强调；箭头与标题线联动 | 预留媒体比例，边界稳定；触控第一次点击即到目标页 |
| 分类索引 | 聚焦/悬停名称更新旁侧真实分类图；图片慢载时保留上一张或中性背景 | 键盘焦点不要被布局滚动触发的伪 hover 覆盖；手机保留可见图卡 |
| 横向目录 | 原生 overflow-x、scroll-snap、按钮和位置反馈，控制随可滚动程度启用 | 保留手指原生滚动、键盘与普通链接；不劫持页面滚轮 |
| 商品多图 | 真实辅图淡切、克制擦入或明确照片切换按钮 | 按意图延迟加载，加载成功才替换；单图/失败不显示坏控件；不能把别的颜色伪称同一变体细节 |
| 快捷查看 | 原生 dialog + 按需请求 Shopify section，展示实际选项与原生商品表单 | 慢载/失败保留完整商品链接；触控/键盘可用，关闭和加入购物车后的焦点正确 |
| 规格/详情披露 | 原生 details、短摘要、实际可售 variant.url 链接 | 控件与商品链接分开；长内容滚动/完整去向；320px 展开不挤压邻卡 |
| 商品大图 | 完整图片链接渐进增强为原生 dialog，图片 contain，明确关闭 | 无 JS 仍可打开原图；视频/模型不套图片逻辑；失败有消息且能关闭 |
| 数量与变体 | 原生 number 的 stepUp/stepDown，依据 min/max/step 禁用边界按钮；实际价格更新后轻反馈 | 不绕过 quantity_rule，不改变变体 ID；购物车异步数量要防并发，不能复制商品页逻辑就当购物车已支持 |
| FAQ/说明 | summary 指示符、字色/边线变化，正文短淡入；可选 `::details-content` 内在高度过渡 | 默认内容原生可展开，复杂过渡仅在支持时启用；不把未支持浏览器的正文裁没 |
| 购物车/阅读窗口 | 短距离抽屉入场、背板淡入、关窗按钮边线、真实 Cart API 状态反馈 | 不拦截结账，不伪造添加成功/购物人数；关闭仍恢复正确焦点 |
| 客服表单 | `:focus-within` 让标签/边线提示编辑区域，原生 required/错误/提交状态清楚 | 不把静态“已发送”当后台收件成功，保留原生表单 |

## 技术取舍

优先 `transform`、`opacity`、细边线与颜色；图片尺寸用 aspect-ratio / 明确宽高稳定布局。通常短反馈从约 120–280ms 开始，照片可略慢，实际看节奏后调整。不要长期给所有元素加 will-change，也不在每个 pointermove/scroll 里测布局或轮询。

用 `@media (hover:hover) and (pointer:fine)` 限定鼠标专属预览，`:focus-visible` / `:focus-within` 提供键盘路径。颜色变化通常可保留；`prefers-reduced-motion:reduce` 下停用非必要位移、缩放、连续旋转、平滑自动滚动，状态即时切换。

现代 CSS 是渐进增强，不是最低浏览条件。`@starting-style` 可为 dialog/popover 的进入建立初始状态，配合离散 display 过渡前核对实际兼容性；`interpolate-size:allow-keywords`、`::details-content` 的高度动画用 `@supports` 包围。关闭动画或不支持时，原生 details、dialog、链接与表单仍工作。不要用一个全局 `*{animation:none}` 破坏原主题依赖的事件。

示例只是局部手法，不规定整站 DOM：

```css
.catalog-link::after { transform:scaleX(0); transform-origin:left; transition:transform .18s; }
.catalog-link:is(:hover,:focus-visible,[aria-current=page])::after { transform:scaleX(1); }
@media (hover:hover) and (pointer:fine) {
  .category-link:hover img { transform:scale(1.02); }
}
@media (prefers-reduced-motion:reduce) {
  .category-link img { transition:none; transform:none; }
}
```

辅助图成功后再设置就绪 class；不要先把主图隐藏再请求第二张。图像浮层关闭时要忽略旧请求的迟到失败，不能清空下一张。动态插入的快速查看内容、购物车片段与 Theme Editor load/unload 要分别考虑；初始化幂等，Observer/计时器可清理。

## 可用本地功能资产

`assets/retail-native/` 包含真实集合/Type 头部链接、图片阅读窗口和轻量 CSS/JS 功能。`scripts/apply_native_retail.py` 是**本技能自编基线 Header 的适配器**，不替换任意店主原主题；不兼容的 Header 应在其原结构中实现同样职责。`prepare_theme.py` 在自己的新副本中调用它，不修改原基线 ZIP 或后台菜单。

功能资产提供几个可编辑的边线/底色/媒体/抽屉反馈，帮助避免遗漏，不代表每站必须使用同一视觉。按本次版式改写、扩充或替换 CSS/markup，保留真实数据、表单与无 JS 回退。不要把此资产的四种导航外观称为四套整站设计，也不要导入一大套闲置第三方 JS 特效库。

## 实际验收

逐项实际操作本次选用的效果，检查快速鼠标跨卡、键盘展开/关闭、真实触控、慢载/失败、减少动态效果、开关关闭和编辑器重载。数量控件验证 min/max/step 与实际提交值；快捷查看验证真实目标变体、422 错误与关闭焦点；大图验证图片加载失败、Escape、关闭后焦点、无 JS 原图去向。截图只能证明外观，不能代替这些操作。

顶部分类另外覆盖：后台主菜单为空 / 有默认 Home-Catalog-Contact / 已包含相同分类；实际集合 / 只有 Type / 两者都无 / 空店；长店名和多个分类；桌面、手机横向捷径及展开菜单；本地化路由、当前项和去重。自动前台导航不等于创建了后台 Menus。

## 官方知识来源

实际使用新能力时复核当前兼容性与文档：

- [Shopify navigation 与原生 menus](https://shopify.dev/docs/storefronts/themes/navigation-search/navigation)、[collections 对象](https://shopify.dev/docs/api/liquid/objects/collections)、[collection / all_types](https://shopify.dev/docs/api/liquid/objects/collection)、[routes 与本地化](https://shopify.dev/docs/api/liquid/objects/routes)。
- [MDN CSS 性能取舍](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Performance/CSS)、[prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion)、[@starting-style](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@starting-style)、[interpolate-size](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/interpolate-size)。

这些链接支持能力与限制；具体品牌风格、搭配和“高级感”仍需本次实际设计与视觉评审。
