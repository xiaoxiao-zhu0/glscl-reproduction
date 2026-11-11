# Renderer routing

Use one shared slide plan and select the output route by the user's actual constraint.

This reference selects a renderer library, not a second skill. Record the choice once in `deck_plan.json`; resume with it unless the user's delivery requirements or a demonstrated capability limitation changes. Native PPTX uses `python-pptx` directly within this workflow. Do not load the bundled Presentations or PPT Master workflow merely to access a renderer. A conflicting mandatory instruction must be resolved explicitly, never silently ignored. The choice of library alone does not establish visual quality.

| Priority | Route | Typical output |
|---|---|---|
| Equations, Mermaid, code, reproducibility; web/PDF delivery | Slidev | Markdown source plus web/PDF; raster PPTX only as disclosed preview |
| Chinese-first native editing, competition or defense draft | Python `python-pptx` | Editable PPTX plus source data/schema |
| Visual concept exploration | Image-assisted | Selected images plus either renderer |
| Maximum visual polish on an existing PPTX | Native PPTX enhancement workflow | Edited PPTX |

Before rendering, represent each page with a renderer-neutral record:

```yaml
id: P03
page_job: Explain how the proposed method protects old knowledge
takeaway: Replay and regularization reduce forgetting
layout: figure_plus_explanation
units: [architecture_figure, short_text, metric_callout, citation]
relationships: [architecture_figure -> short_text, metric_callout contrasts baseline]
data_sources: [results/ablation.csv]
assets: [assets/generated/P03/hero-v1.png]
motion_plan: reveal the method stages in two steps; complete static frame remains legible
speaker_notes: Explain the trade-off in one sentence
```

At deck level, retain `visual_brief`, `layout_roster`, `asset_plan`, and `motion_target` before choosing the renderer. These fields prevent a static renderer from silently replacing an image-led or motion-led design with a text-and-card draft.

The native PPTX route should keep text, tables, charts, and shapes as editable objects where practical. If a generated image contains exact labels or scientific notation, replace those labels with native text or code-generated overlays before export.

For a PPT/PPTX request without another explicit constraint, choose native PPTX. This also applies to a small editable sample; sample size does not imply raster delivery. For a request for sample images only, rendered PNG/PDF pages are sufficient. Do not add an image-only PPTX as though it completes native authoring.

A Slidev render can establish composition, but reconstruct the accepted layout with native objects if the requested final is editable PPTX. Reuse illustrations and source data rather than regenerating them. Keep exact text, callouts, interface labels and simple relationships native; use native tables/charts for suitable tabular/series data. Complex scientific image panels, meshes and heatmaps may remain raster/vector assets, with their data and reproducible builders supplied and raster exceptions disclosed in the plan. Do not rasterize a whole page merely because one scientific panel needs it.

Declare `delivery.pptx_mode` as `native` or `raster-preview`. A deliberately requested full-slide image deck may use `raster-preview` at final stage only with `raster_authorized: true` and the user's actual request in `raster_reason`. Never infer that authorization from a generic request for a PPT or attractive images.
