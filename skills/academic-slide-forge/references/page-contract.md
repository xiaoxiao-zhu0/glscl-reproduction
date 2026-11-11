# Deck contract, version 2

Write one `deck_plan.json` at the deck root. Paths below are relative to that file, independent of shell cwd. It is the plan and acceptance record, not a new slide renderer. Keep the freely written visual rationale; fields are not a fixed prompt template. Version 2 adds semantic and delivery checks; legacy plans must be migrated and reviewed, not merely relabeled as passed.

```json
{
  "schema_version": 2,
  "project_analysis": "Research object, problem, method, evidence, limitations, audience and reusable source assets.",
  "presentation_intent": {
    "use_context": "Audience and whether the deck is projected, defended or read independently",
    "emphasis": "What the user wants the audience to understand, and which scope matters",
    "visual_expectation": "What the images should explain or show, grounded in the dialogue",
    "explicit_preferences": ["Current user requirements affecting content or layout"],
    "assumptions": ["Only consequential choices not established by sources or conversation"]
  },
  "design_synthesis": {
    "story": "The source-grounded argument this audience should retain",
    "audience_priorities": "What the audience needs explained or demonstrated",
    "visual_needs": ["Explain the actual transformation using a labeled process diagram"],
    "visual_language": "Project-specific composition, medium and style rationale",
    "density_policy": "Requested reading density, content retained on-slide, image/text balance and useful page-level exceptions",
    "delivery_rationale": "Native PPTX so the user can revise main content"
  },
  "renderer": "python-pptx",
  "theme": {"rationale": "Why this project's visual direction fits its audience"},
  "delivery": {
    "stage": "sample",
    "format": "pptx",
    "artifact": "sample-editable.pptx",
    "pptx_mode": "native",
    "review_tracking": "sha256-v1",
    "review": {"status": "pending", "notes": ""}
  },
  "pages": [
    {
      "id": "P01",
      "page_role": "method",
      "takeaway": "The one point this page establishes",
      "audience_question": "Which question does this page resolve?",
      "evidence_focus": "Specific source section, figure/table ID or measured value supporting this point",
      "transition": "What the preceding page established; what this page adds; what question follows",
      "composition": "Reading order and correspondence between visible image states and native annotations",
      "evidence": ["sources/project-summary.md"],
      "layout_intent": "Focal subject at left; readable title at right",
      "visual_reason": "How this subject explains the project",
      "visual_mode": "mixed",
      "visual_units": [
        {
          "role": "explanation",
          "production": "native",
          "purpose": "Explain the documented input-to-output transformation",
          "project_anchor": "sources/project-summary.md: specific module and member responsibility",
          "relationship": "Input, operation and output connected according to the actual method",
          "claim_boundary": "Conceptual process; not a measured result",
          "source_paths": ["sources/project-summary.md"]
        }
      ],
      "image_required": true,
      "asset_paths": ["public/generated/P01-hero.png"],
      "authoring_files": ["build_deck.py"],
      "asset_refs": ["public/generated/P01-hero.png"],
      "preview": "previews/P01.png",
      "visual_review": {"status": "pending", "notes": ""},
      "semantic_review": {"status": "pending", "notes": ""},
      "editable_text": ["The one point this page establishes"],
      "native_objects": {"shapes": 2},
      "raster_exceptions": ["Generated subject illustration; labels and relationships are native"],
      "motion": {"requested": false, "implemented": false, "evidence": ""}
    }
  ]
}
```

## Meaning and evidence

- `design_synthesis` is the model's bridge from project analysis to design: story, audience priorities, nonempty visual needs, visual language and delivery rationale. Values are freely written and derived for this project, not selected from a rigid template. Do not invent evidence to satisfy the chosen design.
- For new or redesigned decks, retain `presentation_intent` and `design_synthesis.density_policy` using short prose or an appropriate small structure. These agent-maintained records connect source analysis to the current dialogue; the illustrated subkeys are examples, not a rigid questionnaire. They are backward-compatible additions to version 2, not new checker/backend capabilities. Record actual questions and answers in `clarifications` when used; do not relabel an assumption as confirmation. Revise affected page/asset plans when the user changes these decisions.
- For new or redesigned decks, use concise `audience_question`, `evidence_focus`, `transition` and `composition` notes where they clarify the argument. These are planning aids, not fixed word-count constraints or automatically scored fields. A source filename alone does not locate the fact/figure being explained. Stable page furniture is welcome; vary the central representation when the content relationship changes.
- `page_role` is a free-form page job; only `cover`, `opener`, `divider`, and `closing` allow decoration alone. Other roles require an explanation/evidence unit. A formula, annotated code excerpt or sourced textual comparison can qualify; generic body prose cannot. No fixed image count or page sequence is required.
- `visual_units` describes substantive visual units, not every icon. `role` is `evidence`, `explanation`, or `decoration`; `production` is `data`, `native`, `generated`, or `supplied`. Generated units cannot be evidence. Split composites when their factual status differs.
- `purpose` and `project_anchor` are required for every unit. Explanation/evidence also needs `relationship`, `claim_boundary`, and nonempty `source_paths`. The anchor identifies a specific source fact or operation; the relationship says what the audience will see, not merely the subject name. Decoration may have no source when it makes no factual claim.
- `semantic_review` requires `status: passed` and concrete notes after inspecting the composed page: visible operation/relationship, grounding, and separation of illustration from evidence. Apply `project-visuals.md`; do not prefill passing reviews.

## Assets and rendering

For deeper visual reasoning, optionally retain `clarifications` at project level. Generated assets require a companion `asset_plan.json`, linked by the deck's top-level `asset_plan` path, with `analysis_basis`, `visual_brief`, and `prompt_review`. New/revised asset plans also use `contract: "asset-contract-v2"` and the explicit candidate/reference/final-use fields in [image-pipeline.md](image-pipeline.md). Keep the link when concepts are retained for provenance but not placed. Asset output paths resolve relative to the asset plan, which may live in a subfolder. These requirements do not change deck schema version 2. The checkers enforce required fields, not their semantic quality; the agent must inspect and record the actual reasoning and results.

- `asset_paths` names real image files; `asset_refs` contains their literal references in authoring source. Both arrays correspond by index. For native builders, record the actual relative path/string used by the generator. This is a source-use check, not proof that pixels are visible.
- `authoring_files` lists relevant Markdown/CSS/components or native builder source. Source references must resolve; do not add dummy comments to pass the checker.
- `preview` is a render of the final composed page, not the isolated generated asset. Set review to `passed` only after inspecting that page; record concrete observations. Use `failed` or `pending` otherwise.
- Whole-page concepts retain `final_role: design_reference` and cannot be final page assets. At sample stage they may be shown on explicitly labeled `sample`/`design_reference` review pages. Final PPTX checks also compare slide-embedded image bytes against known concept hashes, so renaming a file or omitting its placement declaration does not count as reconstruction. This does not detect re-encoded lookalikes or prove that a cropped component is scientifically correct; inspect the real render.
- `motion.evidence` describes tested click states or native effects and static treatment. The checker validates that an implementation review was recorded; it does not execute animations.
- `evidence` lists real source files for content. It proves source availability only, not numerical or medical correctness. Inspect those separately.

## Delivery

- `delivery.stage` is `sample` or `final`, matching user scope. A full-deck request continues after samples; a sample-only request does not expand automatically.
- `format` is `pptx`, `pdf`, `png`, or `web`. `artifact` is the nonempty delivered file (for PNG link one preview while each page has its own `preview`; for web use its local entry file). Multiple delivery formats may use separate plans with one primary artifact per plan. Report only formats actually verified.
- For PPTX, `pptx_mode` defaults by authoring policy to `native` and must be recorded explicitly. Use `raster-preview` only for disclosed previews or explicitly requested image decks. Always give `raster_reason`; at final stage also require `raster_authorized: true` based on the user's actual explicit request, recorded in that reason. A generic PPT request is not this authorization.
- For native PPTX each page supplies nonempty `editable_text`: actual main title/body/essential labels expected as native text, not just page numbers. The checker compares these anchors to that slide's XML. Include all physical slides in order, including stepped reveals, so counts and anchors correspond.
- `native_objects` asserts minimum `charts`, `tables`, `shapes`, or `diagram_shapes` counts, checked against the actual PPTX XML. `shapes` includes text boxes; `diagram_shapes` counts non-textbox shapes and connectors. New/revised native mechanism pages must declare at least one nonzero `diagram_shapes`, charts or tables count, for example `{"diagram_shapes": 6}` only when six real diagram objects were built. A title text box cannot satisfy this gate. Ordinary formula/evidence pages do not need arbitrary diagram shapes. `raster_exceptions` explains complex panels retained as images; it cannot justify flattening the whole page.
- Method/state-change pages record `mechanism_visual` with `input_state`, `operation`, `output_state`, `visible_relationship`, and `implementation` (`native`, `mixed`, or `supplied`). `generated` alone fails the mechanism gate. At least one explanatory/evidence unit must use native/data/supplied production; generated decoration plus title text is insufficient. The check applies whenever `mechanism_visual` is present as well as to `page_role: mechanism`, so changing the role name does not remove it. Agent inspection must still verify that the native objects actually carry the claimed relation.
- For PPTX, `preview` must be rendered from the delivered PPTX, not merely a different Slidev/PDF source. `delivery.review` requires `status: passed` and notes describing actual export rendering and editability inspection. If no suitable renderer is available, keep it pending and report that limitation.
- ZIP/XML inspection cannot detect hidden/off-slide text or prove practical editability. Inspect rendered pages and, when an editing app is available, test representative text/chart/table edits in a temporary copy. Do not claim interactive verification if only structural checks ran.

## Review freshness

New and revised plans set `delivery.review_tracking: "sha256-v1"` before inspection. After rendering the actual deliverable and inspecting each page against sources, record observations sequentially (one plan writer):

```powershell
python <skill-dir>/scripts/review_state.py --plan <absolute-deck_plan.json> --page P01 --kind semantic --notes "Observed relationship and its source; claim boundary checked"
python <skill-dir>/scripts/review_state.py --plan <absolute-deck_plan.json> --page P01 --kind visual --notes "Observed reading order, image-label correspondence, crop and text readability"
python <skill-dir>/scripts/review_state.py --plan <absolute-deck_plan.json> --kind delivery --notes "Actual rendering method, inspected export and editability observations"
```

Replace the example notes with real observations. The helper records `status`, `notes` and a SHA-256 `snapshot`; it does not perform inspection or decide whether a page is good. It binds page reviews to the page plan, project/design/delivery settings, evidence, unit sources, authoring files, assets, preview and delivered artifact. Export review covers the entire plan and all those files. Review records are excluded from hashes so recording another review does not invalidate prior records. Changed inputs or a rebuilt PPTX invalidate affected reviews; shared builder/export changes conservatively invalidate all page reviews. Re-render as needed, inspect changed material and refresh records; never blindly re-stamp old notes. Missing files cannot be stamped.

Legacy version 2 plans without `review_tracking` retain structural compatibility when checked without `--require-fresh-reviews`, but have no review-freshness guarantee. The new-deck workflow uses that flag so missing tracking cannot silently pass. The hashes establish file versions, not truthful review or proof that a preview came from that export. Actual rendering and inspection remain mandatory.

Run `python <skill-dir>/scripts/check_deck.py --plan <absolute-deck_plan.json> --require-fresh-reviews` after composing and reviewing pages. It writes `deck-check.json` beside the plan and exits nonzero on missing structural/review evidence or native PPTX mismatches. This cannot judge aesthetics, relevance, scientific accuracy or playback. Inspect the actual PDF/PPTX separately using the export runbook.
