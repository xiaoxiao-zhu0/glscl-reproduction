# Motion plan

Motion is a communication device. Use it to control attention, reveal a process, or preserve continuity between pages.

## Renderer capabilities

| Renderer | Reliable behavior | Limitation |
|---|---|---|
| Slidev | Slide transitions, progressive reveal with `v-click`/`v-clicks`, and Vue/CSS motion such as `v-motion` | PDF is static; PPTX export may not preserve all interactive behavior |
| Native `python-pptx` | Static editable objects and stepped slide sequences | It does not reliably author PowerPoint animation timelines |
| PDF | A single static frame per page | No interactive motion |

For Slidev, keep motion in the source and provide a readable first frame. For native PPTX, either record the intended animation for a final PowerPoint polish pass or simulate a simple reveal with sequential duplicate slides. Do not claim that an exported PPTX contains animation unless it has been checked in PowerPoint.

## Per-page motion spec

```text
motion_goal: reveal method stages
initial_state: title + input context visible
step_1: show stage A
step_2: show stage B and highlight the change
transition: short fade or directional continuity
static_frame: complete page remains understandable without clicks
```

Prefer one motion idea per page. Use progressive reveal for pipelines, comparisons, and explanations; use a calm transition for section dividers; use no motion when it would distract from a dense table or formula. Keep durations short and consistent, and never hide the only copy of a critical value behind an effect.
