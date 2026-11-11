# Verified upstream lessons

Reviewed 2026-11-07. Links target mutable upstream branches. This file records mechanisms inspected, not benchmarked quality or installed integrations. No upstream implementation or prompt templates were copied.

## Banana-Slides

Sources: [AI service](https://github.com/Anionex/banana-slides/blob/main/backend/services/ai_service.py), [prompts](https://github.com/Anionex/banana-slides/blob/main/backend/services/prompts.py), [quality-control tests](https://github.com/Anionex/banana-slides/blob/main/backend/tests/unit/test_image_quality_control.py).

Verified: ProjectContext carries source context; page descriptions precede image prompts; `generate_style_from_content` derives style from content; the image generator accepts template and material references. Its image prompt asks the model to compose an entire slide, including text. Optional image review evaluates the generated slide against its generation prompt and retries within a limit; this does not itself verify source-grounded claims (the inspected review prompt does not use the supplied page-description/outline arguments); tests show this quality-control setting defaults to off.

Adopt: content-driven art direction, explicit per-page visual descriptions, deliberate reference roles, and inspection of actual rendered results. For academic delivery, use whole-page concept mockups only when useful, then preserve exact facts and editable text in the final renderer. Do not assume screenshot-style generation provides editable objects or scientifically accurate anatomy.

Not implemented here: image-edit/reference-image API input, automatic external vision-review service, or Banana's application/backend. The current relay adapter sends text prompts; mentioning a local reference path in a prompt does not transmit the image.

## ai-ppt-generator

Sources: [README](https://github.com/yuyuanweb/ai-ppt-generator), [single-page workflow](https://github.com/yuyuanweb/ai-ppt-generator/blob/main/backend/app/workflows/slide.py), [quality checks](https://github.com/yuyuanweb/ai-ppt-generator/blob/main/backend/app/domain/quality.py), [flex layout](https://github.com/yuyuanweb/ai-ppt-generator/blob/main/backend/app/domain/flex_layout.py).

Verified in code: preparation trims page-specific evidence; generation produces structured drafts; validation receives concrete issues; the graph allows one repair round. Quality checks cover duplicate content, unsupported numbers, thin content, and empty phrases. Flex layouts distinguish content blocks from row/column containers and restrict bleed for text. The README describes ARQ/semaphore concurrency, per-page retry, SSE progress, and shared content/layout/theme data; those concurrency internals were not audited in this pass.

Adopt: separate content/layout/theme, bounded local repair, page-specific evidence, and structural checks before declaring success. Avoid rewriting an entire deck for one broken page. Our JSON contract and checker are a small independent implementation, not this project's solver or native renderer.

Not implemented here: ARQ/Redis/SSE, layout solving/font metrics, duplicate semantic detection, or automatic claim-to-source verification. Our image runner now independently supports bounded thread-pool request concurrency, validated content-aware reuse, per-asset state saves and local child-process deadlines; it does not implement those application services. A production web application is unnecessary for a local skill.

## PPT Master

Inspected local sources: `ppt-master/workflows/generate-pptx.md`, `ppt-master/references/executor-base.md` as linked authority, and the previously read visual-review stage.

The generation authority places images before page authoring, calibrates font roles, runs early/final checks, and ties final image readiness to actual image placements. The final checker/report participates in export acceptance. Visual review is a separate opt-in stage, and preview is explicitly a side process, not a task completion condition.

Adopt: asset readiness before composition, early representative-page validation, separate structural and visual checks, and final artifacts as completion evidence. The three representative-page sample approach is our adaptation, not PPT Master's exact five-page cadence. Do not copy all its roles, gates, or SVG-specific commands into a Slidev task.

## Slidev

Sources: [README](https://github.com/slidevjs/slidev), [export guide](https://sli.dev/guide/exporting). The locally installed CLI help was checked in this chat.

Use as a renderer with themes, Vue, formulas, diagrams, and motion; it does not supply project analysis or automatic art direction. Dev, web build, and file export are different operations. Pin a working environment and verify the actual requested format. A successful export process can still yield blank pages.

## PPTAgent

Source: [current skill runtime](https://github.com/icip-cas/PPTAgent/blob/main/skills/pptagent/scripts/pptagent_runtime/core.py). Distinguish this current skill implementation from older research versions/tags.

Verified: `record_slide_review`, `review_gaps` and `finalize` track reviewed input snapshots and artifact versions, and reject missing/stale records. Adopted independently in `review_state.py`: bind recorded reviews to plan/file hashes and reject stale snapshots in the local checker. This does not automatically judge the page. Do not import its platform-specific runtime wholesale into this Windows workflow.

## Paper2Slides

Sources: [content planning](https://github.com/HKUDS/Paper2Slides/blob/main/paper2slides/prompts/content_planning.py), [image generator](https://github.com/HKUDS/Paper2Slides/blob/main/paper2slides/generator/image_generator.py), [state/checkpoints](https://github.com/HKUDS/Paper2Slides/blob/main/paper2slides/core/state.py).

Verified in the inspected source: planning names source figures/tables and the focus within them; generation calibrates initial slides, then uses a bounded thread pool and per-result callbacks for remaining pages. Its generator actually passes a rendered reference image to later generation. Pipeline state can resume from available analysis/summary/plan stages; that is not proof of per-asset semantic cache correctness.

Adopt: specific source focus, early composed sample calibration, bounded concurrency and immediate result saving. Do not copy its fixed content-length minimums, full-slide raster route or an automatic outline unsuitable for this project's audience. Our text-only relay uses small written style anchors; it does not implement Paper2Slides' reference-image conditioning. Signature-aware cache validation is our local safeguard, not a claimed upstream capability.

## Verification boundary

Structural checking and mock tests validate mechanics, not aesthetics. The version 2 local gate additionally records analysis-to-design synthesis and semantic reviews, inspects actual PPTX text/object counts, and checks file-version freshness for tracked reviews. These are local safeguards, not upstream integrations or automated semantic judgment. Real rendered representative pages still need review against project facts and the user's visual expectations. Do not report that this study alone makes future decks high quality.
