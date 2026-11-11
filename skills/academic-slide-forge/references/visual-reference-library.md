# Domain reference research and generation inputs

Use this when the user requests a material library, domain-aware visual research, reference-conditioned generation, or improvement of weak generated imagery. Work from the current workspace; do not hard-code another project's library or scientific facts.

## Separate research from generation

Record the user's generation mode in project preferences/checkpoints. Research-only references support domain study, source verification and the library; they are not automatically image-model inputs. In prompt-only mode, synthesize the prompt from verified project facts, the intended explanation and explicit verbal preferences. Do not upload reference images (including sketches or prior outputs), encode their layouts/sample imagery into prose, or use an earlier reference-conditioned prompt as the new starting point. Keep research citations outside the runner's `reference_images` field. In reference-conditioned or edit mode, use only the images and roles authorized for that use. A later explicit request to edit from a picture can change the mode for that job without changing unrelated jobs. This controls supplied inputs; it does not prove zero influence on an LLM that previously saw references.

执行时分开保留“资料库/参考审核”和“项目事实/生成提示词”。prompt-only 提示词逐项追溯到项目来源、页面任务或用户明确的文字风格偏好；若某个样本、布局或隐喻的唯一依据是参考图，就从生成提示词移除。资料库可帮助理解领域和识别错误，不是隐式套版输入。参考图通过只批准已声明用途，生成结果还需单独审核。

## Gather, inspect, and index

Start with figures, photos, diagrams and rendered outputs already in the project. Separate authoritative project assets from literature references, generated illustrations and decorative stock. Seek primary papers and official repositories that address the visual problems at hand: selection, comparison, spatial relationships, causality, internal structure or experimental evidence. A related title alone does not make a useful reference.

Verify the downloaded document's title and identity. Render relevant PDF pages and inspect actual pixels; text extraction cannot reveal composition, clipped labels or arrow placement. Make clean crops without cutting legends, branches or sample groups. Inspect crops at readable resolution, using contact sheets for triage and individual views for dense or questionable figures. Fix clipped crops before conditioning generation on them.

Keep a searchable manifest with source title/URL, local PDF, one-based page/figure, crop rectangle and coordinate system, file dimensions, SHA256, category, visual review notes, useful expression and forbidden semantic transfers. Cite the original paper, not an image search thumbnail. Public availability is not a reusable-asset license: retain uncertain paper figures as research references and create original work for delivery. Record a verified license when direct reuse is intended.

## When the user wants to approve references first

User-provided reference images are optional. Search independently from the project's domain, intended message and visual needs; start with verified local sources and extend to primary papers, official galleries, repositories or licensed asset sources where gaps remain. Inspect the full-resolution images and remove weak or redundant candidates before asking the user to review them.

If the user requests approval before production, save `reference_workflow: user-review-before-generation` in the project checkpoint or review manifest. Carry it forward on resume until the user changes it. This gates all image-model calls for the affected work, including exploratory generation, paid compatibility tests and regeneration. Reading, searching, downloading, rendering, cropping and original native sketches can continue. Do not apply this gate to unrelated projects that did not request it.

Prepare a manageable visual shortlist, usually a few candidates per intended figure rather than a dump of the entire library. Give each a stable ID, readable thumbnail, source link, intended figure/role, specific useful visual feature, recommendation, and forbidden semantic transfers. State whether selection is for research/library use or image conditioning. If conditioning is proposed, show the actual pixels proposed for upload; show a sanitized derivative alongside its source if that is the intended input. Include the planned output types so the user knows what selecting the reference authorizes.

Ask the user to approve IDs, reject IDs, or request a different direction. A reply such as "use A1 and C2" or "use your recommended set" approves the identifiable displayed set; missing answers, elapsed time, prior recommendations and agent quality checks are not approval. Do not imply a standalone HTML selection has reached the agent: ask the user to submit/copy their choices in chat unless a real connected submission mechanism exists.

Record the user's actual reply, selected IDs, approved roles, file hashes and affected output scope in a project review manifest. Partial approval unblocks only that scope. Reuse this approval without asking again for those unchanged references within that scope. A changed uploaded image, role, or materially different output scope needs a focused review of the change; ordinary native labels/cropping/composition within an approved role do not require restarting the whole review. This is an agent-managed workflow record, not an automatically enforced image-runner capability.

After approval, continue within the authorized scope and current generation mode. Research-only approval leaves references in the library; generate from the project-derived prompt without image inputs or copied reference layouts. Pair references with project structure only when conditioning was authorized. If all candidates are rejected, search and present another shortlist. Keep pending references out of live requests. Reference approval authorizes only the stated use; it does not approve generated results or license reuse of third-party artwork.

## Assign roles to selected inputs

For each generated explanation, derive the factual topology from source code, methods or validated outputs. Create a compact original wireframe when useful for planning; do not upload it in prompt-only mode. When reference conditioning is selected, pair project structure with one or a few inspected references that solve a specific visual problem. Do not upload an undifferentiated reference pile.

Declare each input's role:

- **Content authority:** which objects, operations, causal directions and invariants must remain correct.
- **Geometry:** which grouping, reading order, local enlargement or comparison makes that relationship readable.
- **Style:** which line quality, sample treatment, palette or material is useful; preserve required scientific distinctions.

For literature references, state what must not transfer: another method's losses, teacher model, task protocol, measured scatter, numerical result or branding. A style reference is not evidence about this project's mechanism. The prompt should identify what the viewer must visibly infer, not merely list subject nouns or flattering adjectives.

Only for authorized conditioning, use `reference_images` in the plan with path/role entries; [proxy-backend.md](proxy-backend.md) specifies actual upload. In prompt-only mode omit this field or leave it empty, and do not pass `--references-json`. Written filenames, image URLs in prose and descriptions of inspected images are not equivalent to sending pixels. Record actual `input_mode`, ordered reference hashes (empty for text-only) and live request outcome. Unsupported routes or failed transfers remain failures, not reference-conditioned results.

## Explore and review

When one weak concept has not established a direction, develop two or three purposeful, independently generated compositions appropriate to the request: overview, mechanism close-up, temporal storyboard, or another materially different visual hypothesis. Keep common identity/style anchors. Do not count crops, recolors, resize operations or native wireframes as additional AI generations. Avoid a fixed quota for every page and do not generate unused downstream assets.

Use the explicit [asset contract](image-pipeline.md#新资产合同与中文示例) for exploration: group IDs, required candidate count, distinct composition IDs/prompts and `user_review_required: true`. The preflight rejects an incomplete candidate roster; runner success only means the set awaits review. Present the actual successful candidates with concise Chinese explanations when requested, then record the user's selected IDs and output hashes. Do not silently choose on their behalf when user review is required. Reuse an existing selection for its unchanged scope.

Review three separate links:

1. **Source to brief:** correct operations, boundaries, timing and disclosure; missing mechanisms cannot be cured by a faithful render of a bad prompt.
2. **Prompt/references to pixels:** actual branch topology, sample identities/counts where relevant, visible decision, usable label space and distinctive project meaning. An HTTP 200 is not visual acceptance.
3. **Pixels to composed sample:** readability at delivery size, crop quality, real text density and correct native overlays. A gallery does not establish final-page quality.

Record concrete defects and disposition: accepted illustration, needs native reconstruction, or rejected. Do not conceal incorrect arrows under cosmetic praise. Use deterministic/native drawing for exact counts, labels, causal paths and data. Generated apparent charts are never measurements.

For repeated samples, make an explicit identity ledger before generation (for example A B C D E F G H → A B C D E F G R). Compare every position in the returned pixels; a highlighted replacement does not prove the other positions stayed unchanged. If this invariant fails, retain the failed concept for diagnosis and produce the precise layer natively. Do not deliver it as a correct method explanation or keep requesting the same counted scene blindly.

Check semantic leakage from visual references independently of prompt compliance. A model can copy a paper's digit thumbnails, model blocks or apparent data even when the prompt forbids them. When the intended role is geometry only, prefer an original abstraction or sanitized visual study that removes those competing semantic cues, retain the source attribution, and record both the transformation and actual uploaded file. Never label a sanitized study as the original paper figure. Reject leaked domain content that misrepresents the current project.

Record actual decoded output dimensions as well as requested dimensions. Backend size parameters are requests, not proof of the returned image size. Bind the visual review to the output SHA256, list material defects, and keep concept acceptance separate from final scientific-diagram acceptance.

Report independent successful design generations, transport test images, crops, placed assets and rendered pages separately. Preserve prior successes and stop unknown-completion retries. Prefer one targeted repair addressing observed defects over unbounded generation.
