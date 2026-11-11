# Project image pipeline

Generated images should serve the page job and fit the deck's design tokens. They are optional assets, not a replacement for exact scientific graphics.

Before generating, apply [project-visuals.md](project-visuals.md) and the prompt critique in [visual-reasoning.md](visual-reasoning.md). Link each generated asset brief to its page's `visual_units`: role, project source, operation/relationship, visible discriminating details, and claim boundary. Resolve consequential factual gaps through targeted questions before requesting the affected asset. For domain reference research and image conditioning, use [visual-reference-library.md](visual-reference-library.md). A topical subject alone does not explain the project's method.

## Choose the production method

For a whole-page design reference followed by component recovery and editable reconstruction, follow [design-first.md](design-first.md). Generate concepts with the same image runner; use selected asset IDs with `--only` to avoid commissioning speculative downstream parts. Concept images are reference artifacts, while recovered crops and supplemental assets are production inputs. The agent performs decomposition and reconstruction; the runner does not.

| Visual need | Preferred method | Reason |
|---|---|---|
| Network architecture, flowchart, timeline | Mermaid, SVG, draw.io, or Vue/CSS | Exact geometry and labels; editable and reproducible |
| Metrics, ablation, confusion matrix, curves | Python, SVG, or a chart component | Values remain tied to source data |
| Formula or notation | LaTeX/KaTeX | Text and symbols stay accurate |
| Icon or simple geometric mark | Existing icon set or SVG | Consistent and deterministic |
| Conceptual scene, scientific metaphor, texture, cutout | Image generator | Visual richness matters more than exact labels |
| Background or atmosphere | Image generator or licensed stock | Use only when it supports hierarchy and contrast |

## Backend policy

Keep the image backend optional and replaceable. Honor the user's explicit backend choice before the default: when the user selects a dedicated image relay, use the configured adapter in [proxy-backend.md](proxy-backend.md), including for whole-page concepts and single assets. Do not substitute the chat provider's native image tool merely because it is available. Without a selected backend, use the built-in image generation capability for ordinary one-off assets. When the user needs local execution, privacy, repeatability, or many variants, allow a local adapter such as ComfyUI's HTTP API, a Diffusers script, or InvokeAI. Do not make the skill depend on a particular model, GPU, or hosted provider unless the user chooses it.

A native stream error such as `Complexity 'high' is not supported for this image model` is a backend parameter incompatibility, not evidence that the slide prompt is too complex. Do not repeat the same failed native call or change the chat model's reasoning effort as a remedy. Resume through the user's selected image relay when authorized; preserve successful assets and select only the failed asset IDs. Record the actual backend/model and next action in the checkpoint so resuming the deck does not return to the failed route.

Do not hard-code a single image model in the deck skill. Use a verified model ID when a specific capability/version matters; `auto`/`latest` uses a heuristic over the relay model list and cannot guarantee the newest model across families. Record the actual selected model in the asset metadata. Use a configured fallback only when discovery fails.

The runner sends the supplied `prompt` and generation settings; it does not synthesize prompts or evaluate reasoning. `check_asset_plan.py` enforces the presence/types of required source/brief/review and policy fields, not their truth or explanatory quality. New/revised plans use the explicit contract below. The following brief dimensions can help develop its free-form prose:

```text
slide_id: P03
use_case: scientific-educational | stylized-concept | productivity-visual
asset_role: design reference | scene | component | local detail | background texture
subject: the project-relevant subject
composition: aspect ratio, crop, focal point, negative space for text
style: medium, palette, lighting, and relation to the deck tokens
constraints: no text, no watermark, no invented measurements, no logos
references: optional style or source images and their roles
```

For component production, retain the component's page placement, required visible state/detail, shared identity/style anchors and native overlay responsibilities in `visual_brief`. Use separate asset entries and output paths for independently usable parts. The runner sends each final `prompt`; it does not split a scene, compose a slide or infer component prompts from these notes. Follow [project-visuals.md](project-visuals.md) for decomposition, then use the existing bounded batch runner without generating unused variants.

For each accepted asset, store it under a stable project path such as `assets/generated/P03/hero-v1.png`. Retain project analysis basis, source references, usage note and revision in the asset plan, alongside the adapter's sidecar containing prompt, actual model, endpoint host, date and hash. Never claim reasoning metadata is generated automatically by the adapter. Never leave a project-bound image only in a global cache.

## 新资产合同与中文示例

新建或修改资产计划时，顶层必须写 `contract: "asset-contract-v2"`。每项明确 `exploration_mode`、`candidate_count_required`、`user_review_required`、`reference_use`、`reference_influence_policy`、`final_role` 和 `native_reconstruction_required`；布尔值使用 JSON 的 `true`/`false`，不能写字符串。以下是可通过结构检查的单张定向概念示例；实际使用时替换项目事实、用途和提示词，不能把示例事实当作项目证据：

```json
{
  "contract": "asset-contract-v2",
  "assets": [
    {
      "id": "P03-concept",
      "output": "design/P03-concept.png",
      "prompt": "为项目的回放记忆机制制作一张横向设计概念图：呈现输入样本、筛选操作和更新后的存储状态三个阶段，让读者能区分改变区域与保留区域。使用简洁插画与清晰层次，给后续原生中文标注预留空间。不生成公式、实验数值、论文标识或密集文字。具体槽位、数量和连接关系由原生图层重建。",
      "analysis_basis": "本例假设项目源文件已经证实回放记忆的筛选与更新过程；实际需替换为具体来源和真实操作。",
      "visual_brief": "用于 P03 的设计探索；页面要解释输入、筛选、更新的关系，不作为实验结果。",
      "prompt_review": "示例提示词包含状态与操作；正式请求前需核对实际筛选规则和保持不变的内容。",
      "asset_role": "design_reference",
      "generation_mode": "prompt-only",
      "page_ids": ["P03"],
      "project_terms": ["回放记忆", "筛选"],
      "exploration_mode": "single",
      "candidate_count_required": 1,
      "user_review_required": false,
      "reference_use": "research_only",
      "reference_influence_policy": "isolated_prompt_only",
      "final_role": "design_reference",
      "native_reconstruction_required": true
    }
  ]
}
```

`single` 表示明确的一张定向资产，不是假装完成多方案探索。需要比较视觉方向时，用两到三项独立资产：将各项 `exploration_mode` 设为 `exploratory` 或 `batch`，填写共同的 `candidate_group` 与一致的 `candidate_count_required >= 2`，分别使用不同 ID、输出路径、`composition_id` 和真正不同的提示词，且 `user_review_required: true`。同一提示词改空格、同一图裁切或改色不构成新的构图方案。检查器能发现同文提示词与重复 ID，实质构图差异仍需看图判断。

`reference_use` 为 `none`、`research_only` 或 `conditioning`。prompt-only 必须使用 `isolated_prompt_only`，不得携带参考图。授权条件生图才使用 `reference-conditioned`、`conditioning`、`reference_conditioning_authorized` 和真实 `reference_images`。这些字段不是用户授权的证明，实际回复与范围仍保存在审核记录中。

`final_role` 为 `design_reference`、`component` 或 `page_asset`。整页概念必须保留 `design_reference` 并要求原生重建；裁切出的可用插画部件另记来源、父图哈希、裁切范围和用途。不要通过改角色或换文件名把整页概念冒充最终页面。

```powershell
python <skill-dir>/scripts/check_asset_plan.py --plan <absolute-asset_plan.json> --require-contract-v2
python <skill-dir>/scripts/prepare_assets.py --plan <absolute-asset_plan.json> --require-contract-v2 --workers 2
```

校验失败先修计划。旧计划可不加严格参数做只读诊断；恢复实际生成前需补齐新合同并重新审核受影响的提示词，不能只加版本号。没有生图需求时不用创建空资产计划。

Runner 为资产 sidecar/state 记录提示词哈希、参考图哈希、候选组、构图 ID、审核标记与最终用途，并在复用缓存时核对合同元数据。修改用途或审核策略后不能静默沿用旧审核记录。候选组成功数不足为 `partial`，生成失败为 `failed`，候选齐备为 `awaiting-review`；无候选组但要求用户审核的单图同样为 `awaiting-review`。`ready` 仅表示本次资产任务完成，不代表视觉验收、机制正确或 PPT 可交付。

`--only` 的 state 只覆盖本次所选任务；重试一张导致候选组显示 `partial` 时不能据此重复生成其他成功图。审核前用完整计划在不加 `--force` 的情况下汇总复用已有成果，并检查组内实际成功数。生成请求、成功设计图、兼容性测试图、裁切件、页面放置次数、最终渲染页分别报告。Runner 不代替用户选择，也不自动审核图像。

## 按证据定位失败

- **项目 → 提示词：** 缺关键操作、混淆贡献或引入其他论文内容，先修事实与 brief；换图像模型不能补回未写清的机制。
- **请求 → 输出：** 参数/路由不支持是适配问题；提示词正确而实际图反复改变样本、拓扑或槽位，才考虑图像模型能力、授权的替代模型或原生精确绘制。记录实际 backend/model、提示词版本与输出哈希，不能仅凭“难看”归因于模型。
- **概念 → 页面：** 图好看但 PPT 排版差、中文太小、关系丢失，是重建或组装问题。对比真实 PPTX 样页与概念，修层次、密度、裁切和原生关系；不得拿生图结果冒充样页验收。

先修具体失败环节，再按现有有界修复策略验证。只有适配、语义、视觉和导出检查分别通过，才扩大制作；结构测试通过不保证最终好看。

## Quality rules

- Do not ask an image model to draw an exact architecture, chart, equation, metric, citation, or dense Chinese text. Compose those elements in the selected renderer around the generated image; use native objects for editable PPTX.
- Request negative space where the slide will place a title or annotation, and generate at the target aspect ratio when possible.
- Keep a consistent subject treatment, palette, and lighting across variants. Use project-approved verbal style anchors; reuse a style image only when reference conditioning is selected. Prompt-only jobs must not inherit a reference's layout or sample imagery through a locked prompt fragment.
- Inspect every generated asset for artifacts, misleading scientific symbolism, accidental text, watermarks, and conflict with the page hierarchy.
- Keep the original prompt and final selected version so the asset can be regenerated without changing the slide source.

## Adaptive prompt synthesis

Generate each image prompt from the current project's story, page job, evidence, and visual role. Keep only a small set of deck-wide anchors such as palette family, text-safe area, aspect ratio, and forbidden text/watermarks. Vary the subject, medium, camera or viewpoint, composition, lighting, and visual metaphor when the page role changes. Reuse a motif for continuity, not an identical prompt for every page.

The prompt plan should explain why an asset belongs on that page. A method page may use a process-oriented illustration, a diagnosis page may use a magnified code-diff metaphor, and a conclusion page may use a lineage or audit-trail metaphor. Do not fill every page with the same generic 3D render or blue abstract network.

## Image-first decoration

For a hero, section divider, method metaphor, or project showcase, create an image brief before writing CSS or drawing placeholder lines. The brief should specify the focal subject, target aspect ratio, crop, text-safe area, palette, lighting, and the visual relationship to the deck motif. Generate a small set of purposeful variants, select one after inspection, and keep the final image visually subordinate to the page takeaway when it is used as decoration.

Use full-bleed images, registered overlays, transparent cutouts, or soft background fields when they make the page feel intentional. Avoid generic stock-like imagery, random 3D objects, and decorative diagrams that repeat what the text already says.

## Current adapter boundary

The configured relay adapter supports text-only generation and actual multipart reference-image upload. Select the project's intended mode before preparing inputs. For prompt-only jobs, omit `reference_images` or leave it empty, do not pass `--references-json`, and write a fresh project-derived prompt without copied reference layouts. Research citations and library paths belong outside generation input fields. Verify the returned sidecar records text-only input and no reference hashes; these are request records, not proof of aesthetic independence.

For authorized reference-conditioned jobs, set `reference_images` entries with `path` and `role` in the asset plan, or pass `--references-json` to the single-image runner. The default reference route is `/images/edits`; a custom relay may require `ASSET_IMAGE_EDIT_ENDPOINT`. Local transport tests establish byte upload and metadata behavior, not remote model support or image fidelity. Inspect a successful live output and its recorded references before expanding the batch. Do not silently drop requested references or switch to text-only after a conditioning failure. The batch runner supports bounded concurrency and signature-based reuse; see [proxy-backend.md](proxy-backend.md) for the contract, deadlines and state records.

A prompt requesting transparency does not guarantee an alpha channel. Inspect the actual file before treating it as a cutout. Use a matching plain background or a deliberately framed panel if no verified masking path is available; any local background removal needs edge inspection before assembly. Text-only generation also cannot guarantee identical anatomy or geometry across states: use a reusable base or exact native/data construction when that consistency carries a factual claim.
