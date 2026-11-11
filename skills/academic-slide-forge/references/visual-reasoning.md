# Visual reasoning and targeted clarification

Read when planning explanatory imagery. Apply only the reasoning relevant to the current project; this is not a fixed prompt, page outline or mandatory set of analysis fields. Keep project facts and clarification records in the project's own plan, not in this reusable skill.

## Establish the whole-project story and presentation intent

Before assigning page jobs or commissioning images, connect the project's problem, inputs, main operations, outputs, contribution boundaries and available evidence. Read across the relevant overview, implementation and results instead of treating a task list or a few domain keywords as the project analysis. Keep this map compact and source-linked; do not audit unrelated modules. Narrow to a member or subsystem only after locating its role in the overall project.

Apply [research-continuity.md](research-continuity.md) for source coverage, conflicting evidence and recovery. Carry source-linked findings and unresolved questions forward; deepen the affected analysis when a page or image needs more detail. Reusing a checkpoint does not make an unverified claim true, and starting a supported sample does not waive verification of the remaining deck.

Use the conversation to distinguish the project's facts from the user's intended emphasis: who will read/watch, what they should understand, which work deserves space, desired level of technical detail, image role, layout density, delivery format and any reference preferences. Record these in `presentation_intent`, identifying explicit requests versus assumptions. Briefly communicate the proposed story and consequential assumptions before generation; this is not a mandatory outline-approval gate.

User corrections override earlier inferred design choices. When the conversation changes the emphasis, density or imagery, update the affected page plan and asset briefs before more generation. Reuse assets only if they still fit. Do not interpret a preference expressed for one deck as a permanent default for every future project.

## Analyze the mechanism before its appearance

Read the relevant sources and outputs before writing a visual brief. Separate established facts, proposed behavior, measured results and unknowns. Cite the specific source supporting the explanation.

For the selected page, explain in plain language:

- What the audience should understand and which source supports it.
- Which entities, states and relationships must be visible to convey that point.
- What distinguishes this project's approach or result from a generic explanation.
- Which limitations or uncertainties affect the depiction.

For a method page, this may mean inputs, operation, outputs and unchanged conditions. For other page jobs, analyze the relevant comparison, evidence or relationship instead. Do not force every project into a process diagram or invent facts to complete a checklist.

Translate that analysis into visible details that distinguish the intended explanation. Assign precise facts to data/native graphics and illustrative appearance to generation. A caption naming a feature absent from the composition does not demonstrate it.

Choose context, mechanism or local detail according to what the audience needs to see. Combine views only when they answer different questions. Image count and detail density are not measures of understanding.

## Clarify consequential gaps

Ask after reading sources when a conflict, missing fact, unclear scope, audience, visual intention or density would materially change the story or image. Do not ask for information already available. Correct technical facts do not resolve whether the user wants a concrete working scene, an internal mechanism, a comparison, or a visually striking overview.

When feedback is “the pictures feel strange”, “not relevant” or similar, identify the affected image and the likely ambiguity: wrong subject, wrong abstraction, misleading metaphor, unsuitable realism/viewpoint, or a disconnected image-text composition. Ask a grounded contrast question when intent remains unclear, such as whether the image should show the actual input/output change or explain the internal operation. Describe how that choice changes the pictured objects and relationships. Do not assume the remedy is another isolated subject, more realism, more pictures or higher resolution.

If density is unresolved and materially affects planning, ask whether this is mainly projected narration, a technical defense with compact evidence, or a document to read independently. If the user already says “tighter, more content”, act on that preference; ask only about a remaining tradeoff such as which technical details to prioritize within a fixed page count. Use these as contextual examples, not a compulsory questionnaire.

Use the available asynchronous user-input tool when possible; otherwise ask in normal conversation. Bundle one to three high-impact questions. State what is already understood, the unresolved distinction, and which page/visual decision the answer changes. Offer concise choices only when they are grounded; allow a free-text answer. Avoid broad questions such as “What style do you want?” when a precise question can resolve the issue.

Separate factual blockers from optional preferences. For an unresolved fact that changes the claim or geometry, hold the affected image/page and continue independent source analysis or other pages. A timeout is not an answer. For an optional visual preference, give the user a reasonable opportunity to reply, then proceed with a stated assumption if needed. Do not add a mandatory approval stop for every prompt, image or slide. If the user asks for no questions, restrict the depiction to supported facts and disclose the unresolved point; do not fabricate a mechanism.

Keep a compact clarification record in the project notes or plan: question, source conflict/gap, affected pages, answer or explicit assumption, and unresolved status. An inferred assumption is not a confirmed fact. Resolve one batch before asking another unless a new critical issue emerges.

## Choose a representation that explains

Choose the representation from the argument: spatial imagery for meaningful depth or structure, diagrams for relationships, comparisons for changes, and sourced charts for quantitative evidence. Use only the relevant options; there is no required visual style or layout sequence.

Do not carry a previous project's visual metaphor into the next by default. Stylization must preserve the relationships being explained. Distinguish a representation problem from insufficient raster resolution: more pixels cannot repair shallow analysis.

Treat user references as evidence of visual preference, not evidence of project facts. Identify what makes the reference useful (depth cues, hierarchy, cutaway, surface treatment, local enlargement), then transfer those properties only where they help the current explanation. Do not copy unsupported structures or promise reference-image conditioning through a text-only adapter.

## Compose the page before commissioning its parts

Write the audience question, a specific source focus and the intended conclusion for each page. Check the transition across a consecutive sample: what is already established, what this page resolves, and why the next page follows. Translate technical terms into audience-facing questions without changing their meaning. Avoid rigid problem/method/results quotas when the actual argument needs another sequence.

Sketch the whole page's reading order, dominant visual and supporting detail at the requested density. Decide which visible objects, states or regions correspond to which native labels, arrows, values or explanations; keep that correspondence explicit in the brief. Before/after views need matched context, viewpoint and scale. A local enlargement should identify its source region. Depth, cutaways and material cues should reveal a meaningful structure or action rather than decorate an unrelated diagram. Set the asset crop and text-safe area from this composition; do not generate a generic hero and squeeze the explanation beside it afterward.

Keep stable typography and page furniture. Adapt the central composition to selection, comparison, transformation, hierarchy or evidence as appropriate; novelty on every slide is not the goal. For compact pages, preserve requested details with visible hierarchy and grouping rather than shrinking every element uniformly.

## Write the brief, then synthesize the prompt

Keep a short per-asset brief alongside the final prompt, preferably in `asset_plan.json`. Free-form `analysis_basis` and `visual_brief` fields may hold the reasoning; existing `prompt`, `output`, `size` and `quality` fields keep their adapter meanings. Extra brief fields are agent records, not new backend capabilities.

Connect source facts and the recorded user intent to the intended visual reading in a short brief: what must be seen, how it explains the takeaway, which layers supply precision versus illustration, and how it fits the page's density and available area. Include only relevant constraints. Exact relationships, measurements and evidence stay in native/data layers. A generic render next to a correct diagram does not automatically form one explanation: specify which object/state/region in the image corresponds to the adjacent explanation. If there is no useful correspondence, replace the image or classify and size it as decoration.

Write a natural, scene-specific prompt from that brief. Describe what is visible and how the eye follows the explanation before adding style adjectives. Choose camera, material, lighting, crop and negative space to reveal the mechanism. Keep deck-wide style anchors small; neither a fixed sentence template nor random styles on every page are required. For a purely decorative asset, record its decorative purpose without inventing a scientific mechanism.

Before sending the image request, critique the prompt and planned composite:

1. **Grounding:** Which source supports each claimed entity, state and relationship? Are proposed steps presented as implemented?
2. **Discrimination:** If the operation were replaced by a neighboring method while keeping the subject, what would visibly change? If nothing changes, the explanatory layer is too generic.
3. **Visibility:** Can the planned view actually show the critical boundary, state change or relation at presentation scale? Does the plan depend on tiny text or prose to rescue an irrelevant image?
4. **Production:** Are precise facts assigned to data/native layers and illustration assigned to generation? Is the composite feasible with the current adapter?
5. **Ambiguity:** Could a viewer mistake illustration for evidence or infer unsupported results or ownership? Resolve consequential unknowns before requesting that asset.
6. **Intent and composition:** Does the depicted situation answer the user's intended question, and does its detail survive in the allotted area? Does the image integrate with the page's explanation, or merely share a topic? If earlier imagery was rejected, name what changes in this brief to address that feedback.

Save a brief `prompt_review` observation in the asset plan, including any repair or remaining uncertainty. A field saying “passed” alone is not a review. Revise the weak reasoning or composition before paying for generation; do not generate many variants of the same weak premise.

## Review the image and the composed page

Use two distinct reviews: first source/intent → brief/prompt, then prompt → generated pixels. Fidelity to a prompt cannot establish fidelity to the project. Inspect the generated asset for the requested visible details, plausible geometry, artifacts and crop suitability. Then inspect the final composite with its native annotations/data. Necessary labels are allowed; the test is whether labels identify a visible relationship rather than merely assert a missing one. Check at normal presentation size, not only zoomed in.

Record what is actually visible and what is missing. A beautiful generic subject can remain decoration, but cannot pass as the mechanism explanation. If the idea is right and the crop/artifacts are wrong, repair the asset. If the geometry, state relation or project claim is wrong, repair the brief, composition or source analysis first. Preserve the existing bounded repair workflow; report unresolved limitations rather than regenerating indefinitely.

