# 写主题前完成三个设计技能的准备

这是用户指定的执行顺序：**安装并核对 → 读取规则 → 作出本店设计判断 → 编写原生主题 → 实际预览与交付。** 安装本身不是已经应用技能或完成审美评审的证明。

模式衔接：精品优先沿用用户认可的历史精品，未指明时以 Cozyster 为基准；约 85% 成熟视觉／结构、15% 局部品类适配是设计取向而非像素评分。三技能用于保持并打磨其构成、字级、色面和完整操作状态，允许复用成熟导航、卡片、PDP 与模块节奏，不要求为差异推翻基线或逐组件另行锁定。基础站仍按 EstateKid 或本次参考，自主设计仍独立组织视觉；各模式继续执行 [图片／商品去重及适用差异要求](site-diversity.md)。保留原生功能和必要可用性，不修改内置源或哈希清单来消除规则冲突。

## 一个入口，三套内置模块

只调用 `$shopify-theme-redesign`。三套规则和必要资源随主技能保存在 `assets/design-skills/`，不用店主依次调用三个技能，也不依赖旧电脑上的全局安装。安装主技能的完整目录即包含这三项；现有外置独立安装可保留作单独用途。

| 用户名称 | 核对的源仓库与技能目录 | 本技能内置入口 |
|---|---|---|
| Taste Skill | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)，`skills/taste-skill` | [design-taste-frontend/SKILL.md](../assets/design-skills/design-taste-frontend/SKILL.md) |
| Design Skill | [gabros20/design-skill](https://github.com/gabros20/design-skill)，`skills/design` | [design/SKILL.md](../assets/design-skills/design/SKILL.md) |
| Garden Skills | [ConardLi/garden-skills](https://github.com/ConardLi/garden-skills)，建站使用 `skills/web-design-engineer` | [web-design-engineer/SKILL.md](../assets/design-skills/web-design-engineer/SKILL.md) |

Design Skill 与 Anthropic 的 `frontend-design` 是两个不同的安装对象；后者可作为额外参考，不能拿它替代或声称已经装了 `design`。Garden Skills 是技能集合，本流程要求其中的前端设计模块；不把已安装该模块说成已经安装整个集合。用户提供其他明确仓库或版本时，以用户指定来源为准，核对后同步名称与检查表，不猜测同名项目。

## 先完成安装完整性检查，再开始写

在 Shopify 技能目录运行只读检查，或由可用文件工具做等价核对：

```text
python -X utf8 scripts/check_design_skills.py
```

脚本默认相对自身定位本技能内的 `assets/design-skills/`，核对来源清单 `manifest.json`、三套源文件的 SHA-256、入口名称和链接资源。`--skills-dir` 仅用于检查另一份完整内置包或修复副本，不用于用外置目录跳过集成验证。返回 `ready: true` 且退出码为 0 后，仍须实际读取规则；完整性检查不证明已应用规则、运行了浏览器、安装了所有运行工具或验证了来源签名。

- 完整内置包直接复用，不反复安装、覆盖或每次联网升级。
- 存在缺项/损坏时先恢复主技能内置资源。必要时使用当前环境的 `skill-installer`，按上表仓库和目录在临时目录准备原包，核对来源和许可证后修复；独立安装命令参数分别为 `--repo Leonxlnx/taste-skill --path skills/taste-skill --name design-taste-frontend`、`--repo gabros20/design-skill --path skills/design`、`--repo ConardLi/garden-skills --path skills/web-design-engineer`。保留原目录副本和用户定制，不能只刷新清单来掩盖未经核对的修改。
- 版本更新先在工作目录核对上游改动与 Shopify 兼容性，再更新内置源、原许可证和清单，随后重跑检查。运行设计脚本时把输出和缓存指向本次工作目录，不改写内置源文件。
- 只有检查成功且适用规则已经读取，才能新建或修改本次主题的 Liquid、HTML、CSS、JavaScript，或生成设计成品。不得先搭页面、交付后再补装技能。只读资料研究可以并行进行。
- 因实际网络、权限或来源不明而无法完成时，说明缺哪一项及真实失败原因；不能悄悄换成另一个同名技能、绕过安全提示、声称安装成功或先写主题。用户已要求本工作流安装这些技能，不再为相同的常规安装反复询问是否开始。

分享时携带主技能完整目录，包含内置三套源、许可证、清单和检查脚本；不要仅分享一个 `SKILL.md`。检查工具实际不可用时，用可用文件工具核对同一内置清单和文件并说明验证范围，不能把别处已安装的技能冒充本包已完整集成。只分享技能目录，不自动附带任何店主身份、凭据或历史站点成品。

## 读取并用于本次任务

检查成功后读取三者的 `SKILL.md`，再按它们的路由读取本次适用参考，不一次性加载全部资料：

- Taste：主体、构图、字体与照片节奏；精品用于打磨成熟基线的精细度，其他模式继续判断构成差异，均实际查看成品。
- Design：导航与购物路径、组件状态、视觉系统及设计评审。新站按照其新页面路由阅读视觉方向、字体、布局、配色、图像、动效和适用页面参考；局部修复只读关联部分。它负责设计意图，不能用原型替代生产主题或代替 Shopify 验证。
- Garden 前端：实现细节、视觉层级与完整操作状态。自主设计已获授权时直接落实合理选择；不因原型阶段的确认步骤重新向店主索要开始批准。

在**本次工作目录**的设计记录中写明采用的技能、具体设计决定、读取的关联参考和实际验证范围；不要把记录、ledger、handoff 或技能文件放进只含 ZIP＋CSV 的最终交付文件夹。Design 的默认产物目录/ledger 不是自动 Git 提交的授权。

三项指导共同服从本次商品和 Shopify 约束：原生商品、规格、购物车、账户、搜索、结账；可编辑模块和完整 Footer；真实目录及已确认经营规则。4/2 主商品网格、轻量 CSS、手机速度和减少动态效果保留。不能为了套营销页版式、通过某个风格评分或增加“随机性”而丢掉购物功能、伪造证明、强加大型动画库或把 Garden 原型 Tweaks 面板放进成品。
