# From project facts to useful visuals

Read before planning content-page imagery. This is an analysis method, not a fixed prompt or slide template. Use [visual-reasoning.md](visual-reasoning.md) for mechanism-level analysis, targeted clarification, representation choice and pre-generation prompt critique.

## Start with the claim, then choose the image

The main process is project-agnostic: **source analysis -> model-written design synthesis -> page jobs -> visual production choices -> composition and review**. Do not start by choosing organ pictures, a renderer template, or a fixed count of generated images. First infer what this audience needs to understand and what the supplied project can actually support.

In `design_synthesis`, briefly capture the story to tell, audience priorities, visual needs, visual language, and delivery rationale. Each visual need should name the concept/evidence to communicate and the chosen representation. These are open-ended decisions, not preset layouts: a mathematical project may need derivations; a software project may need data flow or a code comparison; an experiment may need plots; a physical prototype may need material or spatial views. The same domain can require different designs for a defense, tutorial or pitch. Keep assumptions and missing evidence explicit. Domain examples are not required outlines.

For each content page, identify the source-backed takeaway, the object being acted on, the actual operation, the relationship/change the audience must understand, and the evidence available. Record these briefly in `visual_units` in the page plan. Preserve team ownership: an upstream network, another member's reconstruction module, and this member's contribution are different claims.

Choose how to produce each layer:

- **Evidence:** actual data, scans, masks, recorded outputs, measurements, plots, or source-grounded comparisons. Retain source paths and relevant case/run/coordinate identifiers. AI imagery cannot substitute for these.
- **Explanation:** a diagram or composite that communicates the actual mechanism, spatial relationship, handoff, or intervention. A generated cutout can supply visual detail; native labels, arrows, overlays and exact topology supply precision. Clearly mark conceptual portions.
- **Decoration:** mood, cover identity, dividers, or supporting atmosphere. It may be attractive and useful, but cannot count as the explanation or evidence on a method/results page.

Generic body prose does not qualify as an explanatory visual unit. A source-grounded formula derivation, annotated code excerpt, or concise textual before/after comparison can qualify when it communicates the actual argument; no extra illustration is necessary. A standalone organ, chip or robot with a topical caption usually remains decoration. Do not solve this by adding arbitrary arrows: their endpoints and meaning must correspond to the project's actual process.

Use the **title-swap check**: if the visual communicates the same thing after replacing the project title with an unrelated project in the same field, identify the missing project operation/relationship. Keep a reusable cover motif if appropriate; rebuild the content-page explanation. Review the composed page as well as each asset: a generic organ cutout can become useful within a precise, grounded explanation.

## Turn the claim into a visible explanation

Before asset prompts, decompose a substantive page into a short explanation: what enters, what is compared/changed/selected, and what follows. Use the relevant relationship for non-process pages. Map each necessary step to something the audience can actually point at in the planned composition. Retain this mapping in the existing page `composition` or `visual_units`; do not add a separate approval form.

A title promising selection needs visible candidates and a selection criterion; a title promising adaptation needs visible conditions and a resulting change. Naming these in boxes is insufficient if the decisive relationship is absent. Use a source-backed local example, aligned states, annotated detail or intermediate representation to bridge the gap. A schematic example must be labeled as such; any illustrative numbers must be internally consistent with the documented rule and must not look like measured results. If the source cannot support the title, narrow the title or resolve the gap.

Content sufficiency means the audience can follow the reasoning, not just recognize the terminology. Keep the project's distinctive operation, the necessary explanation of symbols, and the relevant evidence/limitations on-page at the requested density. A beginner audience often needs more concrete intermediate explanation, not fewer facts. Do not replace missing reasoning with extra slogans or put the entire explanation into speaker notes.

## Choose scene or component production

For image-led visual exploration, use [design-first.md](design-first.md) before final component production: generate and inspect the whole-page design, then recover reusable parts and supplement missing ones. This establishes the composition and appearance before commissioning its parts; it does not change their factual roles.

Choose an asset's scope from its job. A whole scene is useful when spatial context or an overall setting carries the meaning. When the page explains selection, transformation, comparison or interaction between parts, prefer a composed explanation with independently placeable components where this improves clarity. A component may be a generated object/state/detail, an existing project image, or a native/data graphic. Do not split a coherent scene into arbitrary icons or impose a generated-image quota.

For component-based pages:

1. Sketch the final page with the explanation steps and reading order. Allocate room for the distinctive details before reserving a large illustration area.
2. Assign each needed component a purpose and page location, the state/detail it must show, its source anchor and its correspondence to native labels or connectors. Group repeated objects/states by identity so the audience can track them. Keep this concise in the existing asset brief; one request produces one independently usable asset, unless an inspected atlas can be reliably cropped.
3. Generate only the visual appearance that benefits from generation. Build exact membership, selection highlights, boundaries, quantities, topology, equations and relationships in the renderer. For example, sample thumbnails can be illustrative assets while the candidate grid, selected subset and criterion remain native. A beautiful storage object alone does not explain selection.
4. Compose the actual components and inspect their combined scale, viewpoint, lighting, crop and label anchors. Before/after views should preserve unaffected context. If independent generations drift, reuse a common base with native overlays where appropriate; do not imply that text-only prompts ensure identical geometry.

During component production, prompt the component rather than another complete slide: specify the relevant object and state, visible distinguishing detail, useful view, bounds, background treatment and exclusions. Keep deck style anchors consistent, but derive the content separately for each component. Whole-page design exploration is a separate stage; its generated labels or scientific relationships are not authoritative content to retain beneath native text.

## Adaptive image brief

Only after choosing the role, derive a free-form prompt from the page analysis. Specify the subject and relevant state, the operation or spatial relation to convey, which details must be supplied by editable overlays, composition and text-safe area, and scientific boundaries. Choose viewpoint and medium for readability; share a small set of style anchors across the deck. Do not lock all projects into the same organ render, color palette, camera, or metaphor.

Make the prompt specific through the current project's entities, states and relationships, rather than a reusable domain scene. Determine the necessary level of detail from the page's argument; keep case-specific instructions in the project asset plan.

Prepare only assets needed by the selected pages. Reuse accepted illustrations if still suitable; lack of relevance is usually a page-analysis/composition problem, not a reason to repeatedly generate prettier subjects.

## Domain-specific detail

Only for medical projects, read [medical-visuals.md](medical-visuals.md) for anatomy, scan/mask alignment and evidence boundaries. Other domains derive their constraints from the current project; do not apply medical requirements to them.

## Review and repair

Record `semantic_review` only after inspecting the composed page. Its notes must identify the operation/relationship actually visible, what source supports it, and whether generated material could be mistaken for measured results. If it fails, repair the responsible layer: source analysis, evidence extraction, explanatory composition, or image brief. Adding more prose or a different generic subject does not resolve a missing explanation.

For a component-based redesign, include a fully assembled explanatory page in the representative sample; an asset gallery or cover cannot validate it. Walk through the visible steps against the title and source. Record any missing link and repair that specific layer before batch expansion. Inspect semantic integration, not merely whether each image is attractive. Reuse the existing sample/review records and bounded repair process.
