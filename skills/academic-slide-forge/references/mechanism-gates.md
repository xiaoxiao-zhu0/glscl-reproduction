# Mechanism and asset contract

Use this gate whenever a page explains a method, interaction, transformation,
selection rule or state change. It is the small contract that keeps a deck from
falling back to a generic picture beside prose.

## Page brief

Write the page's visible logic before choosing an image:

```text
input_state -> operation / decision -> output_state
visible_relationship: what the audience can point to
native_layers: labels, exact topology, equations, values, or data supplied by the renderer
```

For a comparison, use `before_state -> changed_condition -> after_state`; for a
hierarchy or evidence page, name the relation that carries the claim. The
brief must name project entities and the source path that supports them. A
title, caption, or arrow that merely asserts a missing relation does not pass.

## Asset brief

Every generated asset has one or more explicit `page_ids`, an `asset_role`, a
`generation_mode`, `project_terms`, and a short `analysis_basis`,
`visual_brief`, and `prompt_review`. An `explanation` asset also records a
`mechanism` object with `input_state`, `operation`, `output_state`,
`visible_relationship`, and `native_layers`.

Prompt-only generation is the default. It has an empty `reference_images`
list and a fresh prompt derived from the project facts. References remain
research material unless the user explicitly authorizes conditioning. A
prompt that only describes an object, mood, palette, or camera is a decoration
prompt, even when its subject uses the right domain noun.

For an explanation asset, do not combine `No arrows`, `No words`, `No numbers`,
and `No charts` when those marks are the only way the requested relationship
would be visible. Keep exact labels, topology and values in native/data layers,
but make the generated layer expose the relevant objects and state change.

## Placement and review

One asset is one independently usable visual. Crops and repeated placements do
not count as independent generations. Reusing an asset across pages requires a
page-level `asset_reuse` object with `allowed: true` and a concrete reason;
otherwise create page-specific assets. Reuse is normally limited to a cover,
background or deliberately shared context and cannot hide a missing mechanism
explanation.

For every content page, set `visual_mode` to `generated`, `native_diagram`,
`data_chart`, or `mixed`. `text_only` is not an accepted content mode. A
mechanism page additionally records `mechanism_visual` with the same four
visible fields and identifies whether the explanatory layer is native,
supplied or mixed; generated-only implementation is rejected. It needs a
native/data/supplied explanatory unit. For new/revised native PPTX, declare
nonzero `native_objects.diagram_shapes`, charts or tables and check actual
objects; title text boxes do not establish reconstruction. A native diagram is valid when it visibly carries
the relationship; a formula or a set of unlabeled boxes alone is not.

Run the deterministic checks before image calls and again before export:

```text
python <skill-dir>/scripts/check_asset_plan.py --plan <asset_plan.json> --require-contract-v2
python <skill-dir>/scripts/check_deck.py --plan <deck_plan.json> --require-fresh-reviews
```

These checks catch missing briefs, forbidden mechanism prompts, undeclared
reference mode, incomplete candidate rosters, repeated images, whole concepts
embedded as final PPTX pages and missing native reconstruction. New/revised
asset plans follow `asset-contract-v2` in [image-pipeline.md](image-pipeline.md);
single focused assets remain valid without exploratory alternatives. They cannot judge
the pixels. The rendered-page review must still state which input, operation,
output and relationship are visibly present and whether the image could be
moved to an unrelated project by changing only its title.
