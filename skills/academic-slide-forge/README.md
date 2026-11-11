# Academic Slide Forge

一个面向学术汇报和项目展示的 Codex skill：先从项目源码建立事实边界，再规划页面叙事、选择可编辑的渲染方式、制作必要素材，并对导出的页面做结构和视觉检查。

这个目录是可独立分发的 skill 包。它不包含任何项目的 PPTX、数据集、模型权重或生成图片；使用时把它复制到 Codex 的 skills 目录，或在仓库中作为共享 skill 引用。

## 包含内容

- `SKILL.md`：主工作流与交付约束。
- `references/`：页面契约、视觉推理、素材流水线、渲染、导出和质量检查等阶段性参考。
- `scripts/`：工作流状态、资产合同、素材准备、图片适配器、页面检查和测试脚本。
- `agents/openai.yaml`：Codex skill 的展示名称和默认调用提示。
- `assets/prompts/`、`assets/generated/`：为后续贡献者预留的生图提示词和输出位置；本次不提交任何真实图片或密钥。

## 使用

在 Codex 中调用：

```text
$academic-slide-forge
```

它会先检查当前项目和已有工作流状态，再根据项目事实生成页面计划。PPTX 请求默认使用原生可编辑文字、形状、表格和图表；只有适合的概念场景、背景或装饰层才使用图片。

## 生图扩展位

生图是可选步骤，不是每页的配额。需要补图时，贡献者可以：

1. 在 `assets/prompts/` 保存项目自己的提示词和来源说明。
2. 在项目目录创建符合 `asset-contract-v2` 的 `asset_plan.json`。
3. 先运行资产计划检查，再调用 `scripts/prepare_assets.py`。
4. 将审核通过的图片放到项目自己的 `assets/generated/<page-id>/`，并保留 sidecar 元数据。

本仓库只留下目录说明，不预置模型、API 地址、图片样例或访问密钥。图片中的精确拓扑、公式、数字和中文标签应由 PPTX/SVG/图表等原生层重建，不能把生成图当成事实证据。

## 本地检查

在仓库根目录运行：

```powershell
python -m unittest discover -s skills/academic-slide-forge/scripts/tests -v
```

图片适配器的凭据只从环境变量或用户目录下的私有配置读取，禁止写入本目录、提交到 Git 或放进提示词文件。

## 许可与来源

提交到仓库前，请按你的仓库许可证补充版权和第三方依赖说明。该 skill 本身只提供工作流、检查器和适配器，不携带任何项目数据或外部图片版权材料。
