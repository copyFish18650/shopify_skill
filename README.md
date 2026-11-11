# shopify_skill

8 个可完整安装的 Codex / Agent Skills：Shopify 原生主题装修、政策与服务页，以及设计、前端实现和界面评审工具。每个技能都保留 `SKILL.md`、参考资料、脚本和所需素材。

## 下载并安装

需要 Git 和 Python 3.8+。Windows 通常使用 `python`，macOS / Linux 可将下面的 `python` 换为 `python3`。

```bash
git clone https://github.com/copyFish18650/shopify_skill.git
cd shopify_skill
python install_skills.py
```

默认复制全部 8 个技能到 `~/.agents/skills/`，这是 [OpenAI 官方文档](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)列出的用户级技能目录。安装脚本只使用 Python 标准库，不需要先执行 `pip install`。安装后新开会话；技能未出现时重启 Codex。

也可以在 Codex 中把仓库链接交给 `$skill-installer`，指定需要的 `skills/<技能名>` 目录安装。

```bash
# 查看技能，或只检查文件完整性
python install_skills.py --list
python install_skills.py --check

# 维护者可运行安装行为测试
python -m unittest discover -s tests -v

# 只安装两个 Shopify 技能（主题技能已内置所需的三套设计资源）
python install_skills.py --skills shopify-theme-redesign shopify-policy-pages

# 安装到某个项目的技能目录
python install_skills.py --dest /path/to/project/.agents/skills
```

如果现有环境使用其他技能目录，传入 `--dest` 即可。例如：

```powershell
# Windows 上使用旧版 ~/.codex/skills 目录的现有环境
python install_skills.py --dest "$env:USERPROFILE\.codex\skills"
```

相同版本重复安装会自动跳过；已存在不同内容时停止并提示。确认替换时增加 `--force`，旧目录会移到目标父目录下的 `.skill-backups/<时间>/`，再安装新版本。

## 技能列表

| 技能 | 用途 |
| --- | --- |
| [shopify-theme-redesign](skills/shopify-theme-redesign/SKILL.md) | 参考站复刻、自主设计、原生 Shopify 主题、商品 CSV、政策及实际首页截图 |
| [shopify-policy-pages](skills/shopify-policy-pages/SKILL.md) | 常规站或精品站政策与服务页，默认手动文案，明确自动模式时保存并验证 |
| [design](skills/design/SKILL.md) | 产品体验、视觉方向、交互、布局、设计系统和设计评审 |
| [design-taste-frontend](skills/design-taste-frontend/SKILL.md) | 网页与应用页面的视觉方向、设计资料库及浏览器检查 |
| [frontend-design](skills/frontend-design/SKILL.md) | 前端页面的视觉设计指导 |
| [ui-ux-pro-max](skills/ui-ux-pro-max/SKILL.md) | 可搜索的风格、配色、字体、可访问性和技术栈指导 |
| [web-design-engineer](skills/web-design-engineer/SKILL.md) | 浏览器可预览的页面、仪表盘、原型与交互实现 |
| [web-design-guidelines](skills/web-design-guidelines/SKILL.md) | 根据 Web Interface Guidelines 评审界面 |

在支持技能的会话中可直接输入，例如：

```text
使用 $shopify-theme-redesign，按我提供的参考站装修一个服装精品站。
使用 $shopify-policy-pages，手动模式生成这家店的完整英文政策及服务页。
使用 $ui-ux-pro-max，为当前项目设计商品管理界面。
```

## 运行环境

- **安装与校验：** Python 3.8+，无需第三方 Python 包。
- **Shopify 主题图像处理：** 按需要执行 `python -m pip install -r requirements.txt`，安装 Pillow。Python 3.8 安装时 pip 会选择兼容版本。
- **Taste 设计脚本与浏览器检查：** Node.js 22+；涉及实际截图检查时还需要 Chrome / Chromium 或该技能支持的浏览器环境。
- **联网与后台操作：** 在目标 Agent 环境提供联网、浏览器或相应连接工具；店铺账号和授权由使用者自行配置。技能目录本身不提供店铺访问权限。

Shopify 主题技能包含 `assets/design-skills/` 中的三套设计资源、原始许可证及 SHA-256 清单，完整安装主题技能即可使用其内置流程。可以另外检查：

```bash
python skills/shopify-theme-redesign/scripts/check_design_skills.py
python skills/ui-ux-pro-max/scripts/search.py "ecommerce navigation" --domain ux
```

执行技能脚本时，以实际安装后的技能目录为准。主题交付默认放当前工作区的 `output/shopify/`，也可以在任务中明确指定其他位置。

这里保留了原技能中的经营规则偏好，例如美国市场、退货/取消、库存配额和折扣选择。使用者应按自己的店铺资料和实际业务明确覆盖这些偏好；商家身份与联系资料需要每家店单独提供。

## 更新

```bash
git pull --ff-only
python install_skills.py --force
```

如果首次安装使用了 `--dest`，更新时传入相同目录。备份位置会显示在终端。

## 来源

第三方技能的来源及原始许可证见 [SOURCES.md](SOURCES.md)。本仓库收录的是已安装版本，可能包含本地调整；未声明与上游最新版本相同。内置快照保持原字节，仓库设置已避免 Windows Git 换行转换破坏其校验值。
