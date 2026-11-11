# OpenAI-compatible image proxy

Use this adapter when the user has a relay URL and API key but no local ComfyUI or Diffusers installation.

When the user explicitly chooses this dedicated image relay, it is the selected generation backend for concepts and assets. The chat provider and its native image tool are separate routes; do not silently use them instead.

## Configuration

The adapter automatically reads `C:\\Users\\Lenovo\\.codex\\academic-slide-forge\\image.env` when it exists. Put the key in that private file, or set the same variables in the local shell. Never write the key into `SKILL.md`, a prompt file, a PPTX, or a committed `.env` file.

```powershell
$env:ASSET_IMAGE_BASE_URL = "https://your-relay.example/v1"
$env:ASSET_IMAGE_API_KEY = "your-key"
$env:ASSET_IMAGE_MODEL = "auto" # heuristic selection from relay-advertised image model IDs
$env:ASSET_IMAGE_FALLBACK_MODEL = "<verified-image-model-id>" # optional; use a supported ID
$env:ASSET_IMAGE_SIZE = "1536x1024"
```

The pre-created private file is:

```text
C:\\Users\\Lenovo\\.codex\\academic-slide-forge\\image.env
```

Fill only the empty `ASSET_IMAGE_API_KEY=` line unless your relay uses a different model or base URL. With `ASSET_IMAGE_MODEL=auto`, the adapter queries `/models`, filters image-capable IDs, and ranks candidates by numbers in their IDs, creation time and name. This heuristic does not prove which model is newest or best across model families; use a verified explicit model ID when that matters. The fallback is used if discovery fails. Do not change a working private configuration merely to match these examples.

On Windows, `ASSET_IMAGE_HTTP_TRANSPORT=auto` (the default) uses `curl.exe` and the system TLS stack when available; elsewhere it uses Python urllib. Use `curl` or `urllib` to select a transport explicitly. This avoids the observed Python `SSL: UNEXPECTED_EOF_WHILE_READING` failure without disabling certificate verification. Credentials go to curl through standard input, never command-line arguments or temporary files. Generation requests are not automatically retried after network failures/timeouts because remote completion may be unknown. The adapter sends `quality` independently and does not send `complexity`.

If direct connections reset and a working local HTTP proxy is available, set `ASSET_IMAGE_HTTP_PROXY` in the private image configuration for the curl transport. This proxy affects only image requests, not the chat provider. Verify the proxy with model discovery first; do not automatically resubmit a generation whose remote completion is unknown.

`ASSET_IMAGE_BASE_URL` should be the API base ending in `/v1` (or the provider's equivalent). If the relay gives a complete images endpoint, set `ASSET_IMAGE_ENDPOINT` instead:

```powershell
$env:ASSET_IMAGE_ENDPOINT = "https://your-relay.example/v1/images/generations"
```

## Single-image transport diagnostic

For new project assets, use the validated batch workflow below, even for one image. The low-level adapter command here tests transport only; it does not enforce the asset contract, candidate requirements or review state. Do not use it to bypass a failed preflight or a pending user review.

```powershell
python "D:\\CodexData\\config\\skills\\academic-slide-forge\\scripts\\generate_image.py" `
  --prompt-file "assets/prompts/P03-hero.txt" `
  --output "assets/generated/P03/hero-v1.png"
```

The adapter sends one image request and accepts the usual OpenAI-compatible `data[0].b64_json` or `data[0].url` response. It also writes a sidecar metadata file beside the image with the prompt, endpoint host, model, timestamp, and hash. It never writes the API key. Set `ASSET_IMAGE_MODEL` to a verified ID or use discovery; the resolved model is sent explicitly.

## Upload actual reference images

Research/library references are not automatically generation inputs. For a prompt-only project, omit `reference_images` or leave it empty, do not pass `--references-json`, and verify text-only metadata. The following upload instructions apply only to authorized reference conditioning or editing.

For reference-conditioned generation, supply inspected PNG, JPEG or WebP images with an explicit role. The adapter sends their actual bytes as ordered, repeated `image[]` multipart fields, together with the prompt/model/size/quality; it does not merely append their paths to prose. It uses the conventional sibling `/images/edits` route unless `ASSET_IMAGE_EDIT_ENDPOINT` overrides it. A nonstandard generation endpoint requires this explicit edit endpoint. The relay/model must support this schema; local tests cannot establish remote compatibility.

In a batch asset entry, add:

```json
"reference_images": [
  {"path": "../sketches/method.png", "role": "Content authority: preserve these verified branches and arrow directions."},
  {"path": "../references/paper-figure.png", "role": "Visual grouping only; do not transfer its algorithm, labels or results."}
]
```

Paths resolve relative to the asset plan. For the single-image CLI, save the array itself in a JSON file and pass `--references-json <path>`; its image paths resolve relative to that JSON. Empty/missing roles, unreadable images and unsupported file suffixes fail locally. Reference roles are prepended to the prompt in input order.

Sidecar metadata records `input_mode`, reference path/role/SHA256 and actual endpoint path. Cache signatures include ordered reference paths, roles, byte hashes and the reference endpoint, as well as normal request settings. A changed reference invalidates reuse. The runner verifies returned metadata before publishing an output. Temporary multipart bodies are removed; credentials remain outside project files and command lines.

First inspect one live output and confirm its recorded input hashes. If the reference route rejects the request, report the safe HTTP/error class and stop that request. Do not silently omit references, switch backend or convert it into text-only generation. A transport failure cannot establish reference fidelity or remote support. Do not automatically retry a request whose remote completion is unknown.

Each asset entry requests one image. Use separate IDs/prompts/output paths for independently useful compositions; cropping one response into several files still represents one original generation. These scripts perform transport and caching, not visual quality review, masking, layer extraction or scientific validation.

If the relay uses a chat/completions endpoint, a different JSON schema, or returns images inside a provider-specific response, keep the skill unchanged and modify only this adapter's request/response mapping.

## Automatic deck generation

During PPT generation, write an `asset_plan.json` next to the deck sources and run the asset preparation step before rendering slides:

```powershell
python "D:\\CodexData\\config\\skills\\academic-slide-forge\\scripts\\prepare_assets.py" `
  --plan "asset_plan.json" --require-contract-v2
```

Example plan (illustrative only; replace the premise with verified facts from the current project). Here the generated asset is explicitly decoration; the dependency operation still needs a separate source-grounded explanatory layer. For method assets, retain the deeper brief and prompt critique described in [visual-reasoning.md](visual-reasoning.md):

```json
{
  "contract": "asset-contract-v2",
  "assets": [
    {
      "id": "P01-hero",
      "output": "assets/generated/P01/hero-v1.png",
      "size": "1536x1024",
      "quality": "high",
      "asset_role": "decoration",
      "generation_mode": "prompt-only",
      "page_ids": ["P01"],
      "project_terms": ["代码版本", "修订"],
      "exploration_mode": "single",
      "candidate_count_required": 1,
      "user_review_required": false,
      "reference_use": "none",
      "reference_influence_policy": "isolated_prompt_only",
      "final_role": "page_asset",
      "native_reconstruction_required": false,
      "analysis_basis": "Cover decoration for a code-version project; makes no claim about actual dependency topology or results.",
      "visual_brief": "A restrained archival still life suggests successive revisions. Exact version relationships belong in native diagrams on the method pages, not in this asset.",
      "prompt_review": "Suitable only as a decorative cover motif. No invented graph, metrics or implied dependency direction; method explanation must be authored separately.",
      "prompt": "为代码版本与修订主题的演示文稿制作封面装饰：一小叠半透明档案薄页轻微错开，展示各层轮廓，以斜上方视角呈现。柔和侧光、克制的中性色与少量暖色强调。主体位于左半部，右侧留出原生中文标题区域。横向 3:2 插画，用于宽屏页面中的局部构图。不生成文字、数字、图连接线、标识或水印；不暗示真实依赖关系或实验结果。"
    }
  ]
}
```

The agent reads sources, writes and critiques the briefs/prompts, then validates the plan with `check_asset_plan.py --plan <absolute-asset_plan.json> --require-contract-v2` and calls `prepare_assets.py` with the same strict flag. The runner checks required contract fields and sends the supplied prompts; it does not analyze the project or validate semantic quality. Keep reasoning fields for review. After generation, inspect the images and compose/review real pages. Reuse requires a matching request signature, matching image-byte hash, a valid decodable image and matching contract provenance, including candidate, reference and final-use policies. A changed request, changed policy or damaged asset invalidates reuse; `--force` deliberately bypasses a match. Legacy sidecars without required signatures/provenance regenerate once. Output paths resolve relative to the asset plan, not the shell directory. See [image-pipeline.md](image-pipeline.md) for the full contract and review states.

The runner requires Pillow and defaults to `--workers 2` (allowed 1–4). Use `--workers 1` if the relay serializes or rate-limits requests; concurrency reduces independent request waiting, not analysis or rendering time. Auto/latest model discovery happens once per batch. Calibrate a small sample first, then generate the remaining assets with project-derived verbal style anchors. In prompt-only mode, do not inherit reference layouts or sample imagery; an approved reference image is not an authorized conditioning input.

```powershell
python <skill-dir>/scripts/prepare_assets.py --plan <absolute-asset_plan.json> --require-contract-v2 --workers 2 --timeout 420
python <skill-dir>/scripts/prepare_assets.py --plan <absolute-asset_plan.json> --require-contract-v2 --only P03-detail P04-comparison --workers 1
```

Each child process has a local deadline (default 420 seconds). There is no automatic retry: a timeout cannot establish whether the relay completed or billed the request. Inspect the recorded state and retry only the appropriate IDs. Successful outputs survive other failures; replacements publish only after image/metadata validation, preserving earlier images if generation fails. All jobs are bounded by the worker limit; a complete batch can take multiple deadline windows.

`<planstem>.state.json` records the selected batch, resolved models, per-job queued/reused/generated/failed status and elapsed time after every completion. Its overall state distinguishes `failed`, `partial`, `awaiting-review` and `ready`; completed reviewable candidates remain `awaiting-review`. None of these states establishes visual acceptance. Queued includes work dispatched to the pool until its result is known. A nonzero exit indicates one or more failures. Re-running an unchanged plan reuses valid successes; `--only` limits work to selected IDs. The state file represents the latest selected run, while sidecars retain durable per-image cache metadata. Before candidate review, rerun the complete unchanged plan without `--force` to aggregate cached successes; a partial subset state is not a reason to regenerate successful images. Provider responses are withheld from runner errors to avoid exposing sensitive content. Use the failure stage and provider's private console for deeper diagnostics without printing keys.

A `<plan>.lock` prevents overlapping runs of the same plan. After abnormal termination, verify the recorded PID is no longer active before removing a stale lock. Different plans must not share output paths; use separate run directories. This is concurrent image-request execution, not a multiagent design or automatic vision-review service.
