# Source coverage and continuity

Use for project-based deck analysis and recovery after interruption or context compaction. Preserve analytical depth while avoiding repeated discovery. This is agent guidance, not an automatic watchdog or proof that sources are correct.

## Establish coverage, then investigate claims

Start with the requested scope, the project overview and a bounded directory inventory. Identify the current specification/paper, relevant implementation or working artifacts, experiment/result records, and existing figures. Explain the overall problem, inputs, principal stages and outputs before narrowing to the requested subsystem. For a non-code project, use the corresponding design documents, work products and evaluation evidence; do not invent code or experiment requirements.

Follow the main workflow across its interfaces. Read the source behind each substantive claim, mechanism and result that will enter the deck. Inspect surrounding definitions and assumptions, not isolated search hits. Deepen the investigation where a missing dependency, unexplained transformation, conflicting value or ambiguous responsibility could change the story. Record why an apparently relevant area is outside the requested scope; never call an unread area verified.

Do not dump the entire repository or bulk-load all skill references. Exclude dependency caches, generated build trees and retired snapshots from initial discovery unless they are needed to resolve a claim. Search specific paths and symbols, then read relevant sections with their context. A truncated output is not a completed read. A short relevant document may be read in full; a long document needs a section map and targeted reads, extending to full reading when its argument requires it. No fixed file count or analysis deadline determines completeness.

Select sources by applicability and provenance, not just recency or filename. A paper establishes what is described, code or a working artifact establishes what is implemented, and a matching run/configuration establishes what was measured. Agreement between copies of the same report is not independent corroboration. For claims about personal contribution, use explicit attribution or the user's account; repository presence alone does not prove authorship.

## Keep one compact checkpoint

During analysis, create or update `research_checkpoint.md` in the deck workspace, or reuse an equivalent existing research record. Update after a meaningful source-reading batch, a decision, a contradiction, or an artifact completion; do not wait until analysis is finished. If the user forbids writing files at this stage, keep an equivalent compact conversational checkpoint and respect that boundary.

Retain only what is needed to continue accurately:

- Current scope and confirmed intent, the whole-project workflow, and a pointer to the authoritative page plan once it exists.
- Evidence entries: the claim or mechanism, exact source locator (section/table/field/function or relevant lines), the observed fact and conditions, and status such as supported, partial, conflicting or not found. For key numerical claims, retain dataset/split, metric definition, unit, experimental budget and aggregation where relevant. Record source revision or observed modification time/size; use hashes when version identity matters. These markers identify potential changes, not correctness.
- Open questions and conflicts, their impact on pages/images, what was already checked, and the specific evidence or user answer still needed. Preserve contrary evidence and known limitations alongside favorable findings.
- Actual stage, existing artifact paths, last substantive advance, and one concrete next action. Record loaded references so recovery does not reload every guide. A promised build is not a completed build.

Use short findings with locators rather than copying source documents into the checkpoint. Keep durable user answers and unresolved facts; a summary is a navigation aid, not a replacement for source verification. The deck plan remains authoritative for page content/design/reviews; link to it instead of maintaining duplicate page plans. Keep execution timestamps and routine progress in the checkpoint, outside `deck_plan.json`, so progress-only updates do not invalidate page review snapshots.

## Decide whether evidence is sufficient

Move from initial analysis to page planning when the relevant whole-project workflow is explained, the proposed core claims have traceable support, and remaining uncertainties have explicit consequences. Verify these conditions in substance, not by filling empty fields:

- The story separates existing background, work actually completed, proposed behavior and measured outcomes. Main method steps and their dependencies are supported to the depth needed for this audience.
- Central quantitative results can be traced to an applicable source. Check units, metric meaning, evaluation protocol and baseline conditions; corroborate headline results against underlying records when available. If only a report is available, say so instead of implying raw-data verification.
- Material contradictions are resolved or the affected claim remains explicitly uncertain/withheld. Missing results are not zero, a development experiment is not a final benchmark, and a proposed component is not an implemented feature.
- Consequential user choices are known, or only the dependent decisions are held for clarification. Existing answers are carried forward.
- Each planned sample page has enough evidence for its own explanation. The rest of the deck retains an explicit verification backlog, so early samples do not silently discard required content.

Continue targeted research whenever a condition fails; do not skip verification to meet a sample deadline. Work on independent supported pages while a factual blocker is being resolved. If the uncertainty undermines the entire central story, resolve or clarify it before composing that story. A provisional working draft must visibly identify unresolved content and cannot count as a verified result or final delivery.

## Resume and detect lack of progress

After interruption or compaction, read the checkpoint and inspect the named artifacts first. Check source versions where claims depend on them. Reopen sources when the needed detail was not recorded, the source changed, contradictory evidence appeared, or a new page/visual needs deeper analysis. Revisit only affected claims and pages. If no checkpoint exists, reconstruct a minimal one from available conversation and artifacts, verify uncertain core facts, and proceed from that state; do not pretend prior work was verified.

Use the execution ledger described in [execution-state.md](execution-state.md) alongside this checkpoint. After two consecutive recorded batches without a new finding, resolved uncertainty or changed production artifact, explicitly diagnose the cause before another broad read. Name the unresolved fact and choose a targeted lookup, a concrete clarification, or the next supported production action. This is a trigger to examine stalled work, not permission to skip reading or automatically declare it complete. If additional research is genuinely necessary, record what it is expected to resolve and continue. Repeatedly reading unchanged sources or repeating an intention to make samples does not count as progress. A changed file hash signals revalidation, not verified new evidence.

Status updates should identify new findings, changed decisions, remaining blockers or actual artifacts. Do not keep announcing the initial plan after each recovery. This guidance cannot repair an underlying context/runtime failure; if recovery repeatedly fails, report the observed failure and available checkpoint without changing unrelated app configuration.

## Verify again at composition and delivery

Analysis does not end factual checking. Before generation, verify the source relationships used in the image brief. During page composition, recheck exact labels, formulas, values and claim boundaries against the relevant sources and the uncertainty record. Before delivery, review the central argument across pages, resolve or explicitly disclose remaining limitations, and perform the existing semantic, visual and export checks. A complete checkpoint, a successful build or a structural checker cannot independently establish factual accuracy.
