# Durable execution, without duplicate planning

Use one deck workspace and one writer. Keep factual findings, locators, user answers, whole-project coverage and open questions in `research_checkpoint.md`; page content/design/reviews remain in `deck_plan.json`. `workflow_state.json` only records execution and file versions. Do not copy the page plan into it. None of these records substitutes for reading sources or inspecting renders.

## Record completed work

After a meaningful reading batch, resolved question or production action, update the checkpoint first, then record the stage, one executable next action and files actually read/produced. Use the environment's working Python executable; paths below are placeholders, not shell commands to run literally.

```text
python <skill-dir>/scripts/workflow_state.py record --workspace <deck-workspace> --stage analysis --finding "Verified the main workflow in specification section 3; unresolved baseline protocol affects P05 only; see checkpoint evidence E04" --source <specification-path> --guide <guide-actually-read> --next "Read the baseline run configuration to resolve E05, then write the evidence-linked page plan"
python <skill-dir>/scripts/workflow_state.py record --workspace <deck-workspace> --stage plan --artifact deck_plan.json --next "Review the P02 mechanism brief against E04 and prepare its sample asset"
python <skill-dir>/scripts/workflow_state.py status --workspace <deck-workspace>
```

Repeat `--source`, `--guide` or `--artifact` as needed. Sources and artifacts must exist and be nonempty; paths resolve relative to the deck workspace unless absolute. `--finding` means a concrete new fact, decision, contradiction or resolved question, with a locator. Do not use promises or generic “analysis complete” as progress. Detailed findings stay in the checkpoint. A source is registered only after reading the needed context, not merely listing or hashing it. A newly loaded guide alone is not substantive progress.

Stages describe the actual work: `analysis` → `plan` → `sample` → `expand` → `validate` → `delivered`. These are not approval gates. Sample-only requests can move from sample to validation; factual corrections can return to an earlier stage. Stage changes require a recorded finding or new/changed artifact, but the helper cannot prove the change is warranted. Keep existing evidence-sufficiency and quality gates. Mark delivered only after the requested artifact, fresh reviews and export checks are complete.

## Resume the next action

1. Run `status`; read the checkpoint and relevant plan sections. Confirm the current request still matches. Check named files instead of rescanning the repository.
2. Changed/missing sources require checking the dependent claims; changed/missing artifacts require checking or repairing the affected outputs. Do not rebuild unaffected pages. Status is read-only and never acknowledges a changed file automatically.
3. If the checkpoint changed since the last record, reconcile it with actual artifacts before recording the updated state. If state is missing or invalid, recover from checkpoint/artifacts; preserve a corrupt state for diagnosis. Never discard existing work to satisfy the ledger.
4. Unchanged recorded guides need rereading only when a relevant rule was lost from context; read that section, not the entire workflow. A recorded path alone does not mean the agent remembers its contents. Unrecorded details needed for a new page still require targeted source reading.
5. Execute the saved next action. If it is blocked, name the fact/tool/answer needed and its page-level impact, then continue independent supported work. Two batches without reported substantive progress trigger this diagnosis, not an automatic jump to rendering or final acceptance.

Do not poll the ledger as a substitute for work. The helper has no timer, no background monitor, no API retries and no independent semantic judge. It only helps when the agent calls it. Keep timestamps outside the page plan so status-only changes do not invalidate its review snapshots. Never register private relay configuration or credentials as source evidence.
