# Generation and acceptance gates

These gates prevent a visual redesign from silently becoming a text-and-card deck.

## Preflight

For project-based decks, apply the evidence-sufficiency conditions in [research-continuity.md](research-continuity.md). Establish the relevant whole-project workflow and trace core claims to applicable sources before composing them. Hold materially unsupported or contradictory claims; continue independent supported pages. Time spent, file counts and a populated checkpoint are not evidence of sufficient analysis. These are agent judgment requirements, not additional checks implemented by `check_deck.py`.

Before generating slides, retain these decisions in the working deck plan:

```text
visual_brief: style, palette, motif, image policy, density target
presentation_intent: requested emphasis, image meaning, reading context, explicit preferences and unresolved assumptions
layout_roster: the visual mode and layout family for every page
asset_plan: generated, supplied, code-native, or none for every visual unit
motion_target: none, Slidev motion, stepped PPTX, or PowerPoint post-edit
renderer: exactly one primary output route
```

For a request that explicitly asks for a visual redesign, the roster should contain several distinct page roles and at least one image-led role for the opener, section divider, method explanation, project showcase, or conclusion when those roles exist. A page may use no image when a chart, diagram, code excerpt, or table is the correct evidence.

## Acceptance

Reject or revise the draft when any of these is true:

- a repeated layout hides the relationship being explained or gives equal emphasis to unequal information; a stable header, footer and shared framing are not defects by themselves;
- adjacent pages repeat topics without advancing a clear question, explanation or evidence chain;
- a declared image-led role contains only placeholder lines, generic shapes, or empty space;
- the user requests generated imagery but the asset policy silently removes it;
- image prompts are copied across pages without a page-specific analysis basis or meaningful visual variation;
- the selected renderer dropped images or motion without reporting the limitation;
- the first frame is unreadable without animation;
- the slide plan claims click or motion behavior but the source contains no corresponding motion directive, stepped-slide plan, or verified PowerPoint animation;
- the visual assets do not share the declared palette, motif, or crop logic;
- a decorative image competes with the page takeaway or contains misleading labels;
- the layout contradicts the user's requested density, hides requested detail in notes, or expands the page count without respecting the requested limit;
- imagery is regenerated after negative feedback without addressing the identified intent or composition mismatch;
- a method/results/content page has only topical decoration plus prose, with no visual explanation or source-grounded evidence;
- a generated image is presented as a measured scan, segmentation/editing result, or simulation output;
- the visual matches the domain but fails to express the project's operation, relationship or evidence (apply the title-swap check in `project-visuals.md`);
- a sample is presented as completion of an authorized full-deck request;
- a native PPTX is claimed but its key text/tables/charts have been flattened into page images, or only the Slidev source is editable;
- the exported deck has not been checked at the target aspect ratio.

Run `scripts/check_deck.py --plan <absolute-deck_plan.json> --require-fresh-reviews` for the version 2 contract, file/source references, recorded semantic/visual reviews, actual PPTX text/object checks, and review freshness when `delivery.review_tracking` is `sha256-v1`. New/revised plans must enable tracking; changed plan/files require reinspection. A legacy plan must be migrated and reviewed before it passes the strengthened gate. The checker cannot assess project relevance, prove object visibility/editability quality, or validate review notes; inspect final renders and perform the editability review for those.

The review should name the failed gate and repair the smallest responsible layer rather than adding more text or more cards.
