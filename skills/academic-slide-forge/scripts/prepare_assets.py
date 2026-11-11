#!/usr/bin/env python3
"""Generate planned assets with bounded concurrency and content-aware reuse."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from PIL import Image
from generate_image import (default_env_file, load_env_file, endpoint_from_env,
                            env_required, discover_image_model, resolve_references,
                            reference_endpoint)
from check_asset_plan import validate as validate_asset_plan


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path, value):
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def image_valid(path):
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except (OSError, ValueError):
        return False


def prompt_digest(prompt):
    return hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()


def contract_metadata(job):
    """Stable, reviewable provenance copied into every published sidecar."""
    refs = job.get("reference_images") or []
    strict = any(key in job for key in ("exploration_mode", "candidate_group", "composition_id",
                                        "reference_use", "reference_influence_policy", "final_role",
                                        "native_reconstruction_required", "user_review_required"))
    return {
        "contract": "asset-contract-v2" if strict else None,
        "asset_id": job.get("id"),
        "generation_mode": job.get("generation_mode"),
        "reference_use": job.get("reference_use"),
        "reference_influence_policy": job.get("reference_influence_policy"),
        "reference_sha256": [ref.get("sha256") for ref in refs if isinstance(ref, dict)],
        "prompt_sha256": prompt_digest(job.get("prompt", "")),
        "candidate_group": job.get("candidate_group"),
        "candidate_count_required": job.get("candidate_count_required", 1),
        "composition_id": job.get("composition_id"),
        "exploration_mode": job.get("exploration_mode", "single"),
        "user_review_required": job.get("user_review_required"),
        "final_role": job.get("final_role"),
        "native_reconstruction_required": job.get("native_reconstruction_required"),
    }


def prepare_jobs(plan_path, plan, require_v2=False):
    contract_errors = validate_asset_plan(plan, require_v2=require_v2)
    if contract_errors:
        raise ValueError("asset plan contract failed: " + " | ".join(contract_errors))
    assets = plan.get("assets") if isinstance(plan, dict) else None
    if not isinstance(assets, list) or not assets:
        raise ValueError("asset plan needs a nonempty assets list")
    jobs, ids, outputs = [], set(), set()
    for i, asset in enumerate(assets, 1):
        if not isinstance(asset, dict):
            raise ValueError(f"asset #{i} must be an object")
        for field in ("prompt", "output"):
            if not isinstance(asset.get(field), str) or not asset[field].strip():
                raise ValueError(f"asset #{i} needs {field}")
        aid = asset.get("id", f"asset-{i}")
        if not isinstance(aid, str) or not aid.strip() or aid in ids:
            raise ValueError(f"asset #{i} has missing or duplicate id")
        output = (plan_path.parent / asset["output"]).resolve()
        if output in outputs or output.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError(f"asset #{i} has duplicate output or unsupported image suffix")
        ids.add(aid)
        outputs.add(output)
        references = resolve_references(asset.get("reference_images", []), plan_path.parent)
        jobs.append(dict(asset, id=aid, prompt=asset["prompt"].strip(), output=output,
                         reference_images=references))
    return jobs


def configure_jobs(jobs):
    endpoint = endpoint_from_env()
    discovered = None
    for job in jobs:
        model = str(job.get("model") or os.environ.get("ASSET_IMAGE_MODEL", "auto")).strip()
        if model.lower() in {"auto", "latest"}:
            if discovered is None:
                try:
                    discovered = discover_image_model(env_required("ASSET_IMAGE_API_KEY"))
                except SystemExit:
                    discovered = os.environ.get("ASSET_IMAGE_FALLBACK_MODEL", "").strip()
                    if not discovered or discovered.lower() in {"auto", "latest"}:
                        raise
            model = discovered
        job["model"] = model
        job["size"] = str(job.get("size") or os.environ.get("ASSET_IMAGE_SIZE", "1536x1024")).strip()
        job["quality"] = str(job.get("quality") or os.environ.get("ASSET_IMAGE_QUALITY", "")).strip()
        request = {key: job[key] for key in ("prompt", "model", "size", "quality")}
        references = resolve_references(job.get("reference_images", []), Path.cwd())
        job["reference_images"] = references
        request["endpoint"] = reference_endpoint() if references else endpoint
        request["reference_images"] = references
        job["signature"] = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


def reusable(job):
    output = job["output"]
    try:
        meta = json.loads(output.with_suffix(output.suffix + ".json").read_text(encoding="utf-8"))
        contract = contract_metadata(job)
        strict = contract.get("contract") == "asset-contract-v2"
        return (meta.get("request_signature") == job["signature"]
                and meta.get("sha256") == digest(output) and image_valid(output)
                and (not strict or all(key in meta and meta[key] == value
                                       for key, value in contract.items())))
    except (OSError, ValueError, AttributeError):
        return False


def generate_job(job, env_file, timeout):
    started = time.monotonic()
    def result(status, error=None):
        value = {"status": status, "elapsed_seconds": round(time.monotonic() - started, 2)}
        if error:
            value["error"] = error
        return value
    try:
        output = job["output"]
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".asset-", dir=output.parent) as temp:
            temp = Path(temp)
            image = temp / output.name
            prompt = temp / "prompt.txt"
            prompt.write_text(job["prompt"], encoding="utf-8")
            command = [sys.executable, str(Path(__file__).with_name("generate_image.py")),
                       "--prompt-file", str(prompt), "--output", str(image),
                       "--env-file", str(env_file), "--model", job["model"], "--size", job["size"]]
            if job["quality"]:
                command += ["--quality", job["quality"]]
            if job.get("reference_images"):
                references = temp / "references.json"
                atomic_json(references, job["reference_images"])
                command += ["--references-json", str(references)]
            completed = subprocess.run(command, capture_output=True, timeout=timeout)
            if completed.returncode:
                diagnostic = (completed.stderr or b"").decode("utf-8", errors="replace")
                # Keep a useful error class without copying provider bodies or credentials.
                safe = re.search(r"Image (?:proxy HTTP \d{3}|HTTP transport failed \(curl \d+\))", diagnostic)
                detail = safe.group(0) if safe else f"generator exited {completed.returncode}"
                return result("failed", detail + "; provider output withheld; no automatic retry")
            if not image_valid(image):
                return result("failed", "generator did not produce a valid image")
            sidecar = image.with_suffix(image.suffix + ".json")
            meta = json.loads(sidecar.read_text(encoding="utf-8"))
            if meta.get("reference_images", []) != job.get("reference_images", []):
                return result("failed", "reference inputs changed during generation; cache not published")
            meta.update(contract_metadata(job), request_signature=job["signature"], sha256=digest(image))
            atomic_json(sidecar, meta)
            # Publish only validated assets. A partially published pair cannot pass reuse.
            image.replace(output)
            sidecar.replace(output.with_suffix(output.suffix + ".json"))
        return result("generated")
    except subprocess.TimeoutExpired:
        return result("failed", "local deadline exceeded; remote completion unknown; no automatic retry")
    except (OSError, ValueError, AttributeError):
        return result("failed", "local image or metadata operation failed")


def run_jobs(jobs, state_path, env_file, workers=2, timeout=420, force=False):
    started = time.monotonic()
    groups = {}
    for job in jobs:
        group = job.get("candidate_group")
        if group:
            groups.setdefault(group, {"required": job.get("candidate_count_required", 1), "candidates": []})
            groups[group]["candidates"].append(job["id"])
    state = {"stage": "generating", "workers": workers, "assets": {},
             "candidate_groups": groups,
             "contract": "asset-contract-v2" if all(contract_metadata(j)["contract"] for j in jobs) else None}
    pending = []
    for job in jobs:
        cached = not force and reusable(job)
        state["assets"][job["id"]] = {"output": str(job["output"]), "model": job["model"],
            "request_signature": job["signature"], "status": "reused" if cached else "queued",
            **contract_metadata(job)}
        if not cached:
            pending.append(job)
    atomic_json(state_path, state)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(generate_job, job, env_file, timeout): job for job in pending}
        for future in as_completed(futures):
            job = futures[future]
            try:
                result = future.result()
            except Exception:
                result = {"status": "failed", "error": "unexpected worker failure; details withheld"}
            state["assets"][job["id"]].update(result)
            atomic_json(state_path, state)
            print(f"{job['id']}: {result['status']} ({result.get('elapsed_seconds', 0)}s)", flush=True)
    failed = any(item["status"] == "failed" for item in state["assets"].values())
    for group in groups.values():
        successful = [aid for aid in group["candidates"]
                      if state["assets"][aid]["status"] in {"generated", "reused"}]
        group["successful_candidates"] = successful
        group["successful_count"] = len(successful)
        group["status"] = ("awaiting-review" if len(successful) >= group["required"]
                           else "incomplete")
    stage = ("failed" if failed else "partial" if any(g["status"] == "incomplete" for g in groups.values())
             else "awaiting-review" if groups or any(j.get("user_review_required") is True for j in jobs) else "ready")
    state.update(stage=stage, elapsed_seconds=round(time.monotonic() - started, 2))
    atomic_json(state_path, state)
    print(f"Assets {state['stage']}; state: {state_path}", flush=True)
    return int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--env-file", type=Path, default=default_env_file())
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=2)
    parser.add_argument("--timeout", type=float, default=420, help="Local per-image deadline in seconds")
    parser.add_argument("--only", nargs="+", help="Generate/reuse only these asset IDs")
    parser.add_argument("--force", action="store_true", help="Bypass matching image cache")
    parser.add_argument("--require-contract-v2", action="store_true",
                        help="Require the current explicit asset policy before any request")
    args = parser.parse_args()
    if not 0 < args.timeout < float("inf"):
        parser.error("timeout must be positive and finite")
    plan_path = args.plan.resolve()
    try:
        jobs = prepare_jobs(plan_path, json.loads(plan_path.read_text(encoding="utf-8-sig")),
                            require_v2=args.require_contract_v2)
        if args.only:
            if set(args.only) - {job["id"] for job in jobs}:
                raise ValueError("--only contains unknown asset IDs")
            jobs = [job for job in jobs if job["id"] in args.only]
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    lock = plan_path.with_suffix(plan_path.suffix + ".lock")
    try:
        with lock.open("x", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
    except FileExistsError:
        parser.error("Plan already locked; verify recorded process has stopped before removing its lock")
    try:
        load_env_file(args.env_file)
        configure_jobs(jobs)
        return run_jobs(jobs, plan_path.with_suffix(".state.json"), args.env_file.resolve(),
                        args.workers, args.timeout, args.force)
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
