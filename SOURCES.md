# 技能来源与打包调整

此仓库于 2026-11-11 从维护者已安装的 8 个技能整理，完整保留参考、脚本与素材。`skills-manifest.json` 记录本次发布文件的 SHA-256；它用于完整性检查，不是上游签名或上游提交证明。

| 技能 | 来源记录与许可证 |
| --- | --- |
| shopify-theme-redesign | 维护者定制的 Shopify 工作流与资源；内置三套第三方模块的来源、原始许可证及逐文件哈希位于 `assets/design-skills/manifest.json` 及各模块目录 |
| shopify-policy-pages | 维护者定制的 Shopify 政策与服务页工作流 |
| design | [gabros20/design-skill](https://github.com/gabros20/design-skill)，已安装版本；附带 MIT 原始许可证 `LICENSE.upstream.txt` |
| design-taste-frontend | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)，已安装版本；附带 MIT 原始许可证 `LICENSE.upstream.txt` |
| web-design-engineer | [ConardLi/garden-skills](https://github.com/ConardLi/garden-skills) 的 `skills/web-design-engineer` 模块，已安装版本；附带原始许可证 `LICENSE.upstream.txt` |
| frontend-design | 已安装的 frontend-design 指令，保留其原有 `LICENSE.txt` |
| ui-ux-pro-max | 已安装并定制的 UI/UX Pro Max 技能；对应上游项目为 [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)，未记录原始安装提交；附带从上游获取的 MIT 许可证 `LICENSE.upstream.txt`，数据文件另保留字体和图标的来源记录 |
| web-design-guidelines | 已安装技能的元数据标记作者为 Vercel；规范来源为 [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines)，技能分发项目为 [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) |

打包时仅作以下兼容调整：

- Shopify 主技能及其自有参考中的固定 `D:/Shopify/模版` 示例改为工作区相对路径 `output/shopify`。
- 独立 UI/UX 技能中的 Claude 插件专属路径改为从当前 `SKILL.md` 定位技能目录的通用写法。
- 为三个独立设计模块补齐主技能已保存的同源许可证；内置三套快照保持不变。
- 排除 Python 缓存、虚拟环境及其他运行缓存，新增安装器、中文说明与发布校验清单。

第三方部分遵守随附的各自许可证；这里没有为全部素材统一更换许可证。参考站截图用于设计研究，不代表参考站代码、商品图片或商标被授予通用商用许可。
