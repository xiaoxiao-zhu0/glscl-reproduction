# Export runbook and timeouts

## Slidev

Use the dev server only for live preview or browser QA:

```powershell
pnpm exec slidev <entry> --port <port>
```

This process is expected to stay alive. Start it in a managed background session with a cleanup path; never treat its continued existence as an unfinished export.

For a bounded delivery export, use a finite timeout and a wait that allows the slide content to hydrate:

```powershell
pnpm exec slidev export <entry> `
  --format pdf `
  --output <output>.pdf `
  --wait-until networkidle `
  --wait 1000 `
  --timeout 120000
```

Slidev `--format pptx` and packaging rendered PNGs with python-pptx produce raster slide decks in the workflow used here; neither is a native editable delivery route. Use them only for a clearly labeled visual preview or an explicitly requested image deck. For native PPTX, author actual text/shapes/tables/charts with a native builder, reusing illustrations and source data. Supply an explicit Chromium executable when the bundled browser is unavailable. Do not use `slidev build` as a substitute for PDF/PPTX export; it produces a web bundle.

## Completion gate

After export:

1. Confirm the requested file exists and is newer than the current run.
2. For PDF, inspect page count with `pdfinfo` or an equivalent parser and render at least one page.
3. For PPTX, inspect the actual ZIP/XML objects with the version 2 deck checker, then render the delivered PPTX with PowerPoint, LibreOffice, or another available PPTX renderer. Inspect every page. A preview from the Slidev/PDF source does not validate a separately built native PPTX. If rendering is unavailable, report the artifact as structurally checked but visually unverified; do not mark its delivery review passed.
4. If the export is blank, retry with `--wait-until networkidle` and a finite `--wait`; do not retry indefinitely.
5. Stop only preview processes owned by this run when no longer needed. Do not stop another task's server.

For new/revised plans, enable `delivery.review_tracking: "sha256-v1"` before review and use `scripts/review_state.py` after inspecting the final page renders and export (see [page-contract.md](page-contract.md)). File or plan changes invalidate the recorded versions; inspect affected content again before recording fresh snapshots. Record `delivery.review` after checking the exported artifact; include object/editability observations, actual rendering method, and limitations. Keep main text as `editable_text` anchors in the plan, not just page numbers or decorative labels. `native_objects` can assert page-level counts for charts, tables and shapes; raster exceptions must be explained. These structural checks supplement, not replace, inspection for invisible text, off-slide objects, crop, overlap and font substitution.

## Failure budget

Use bounded retries: one retry after adjusting wait settings, then report the actual stage and error. A long-running server, browser session, or network request without a deadline is a workflow bug.
