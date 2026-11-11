"""Durable execution ledger; detects changed inputs, never certifies slide quality.

Single writer per deck workspace. No network calls or image requests.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

STAGES = ("analysis", "plan", "sample", "expand", "validate", "delivered")
STATE = "workflow_state.json"


def fingerprint(path):
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing or empty file: {path}")
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_state(root):
    path = root / STATE
    if not path.exists():
        return None
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("version") != 1 or state.get("stage") not in STAGES:
        raise ValueError("Unsupported or invalid workflow state; preserve it and recover from checkpoint")
    return state


def record(root, stage, next_action, finding="", sources=(), guides=(), artifacts=()):
    if stage not in STAGES or not next_action.strip():
        raise ValueError("A valid stage and concrete next action are required")
    checkpoint = root / "research_checkpoint.md"
    fingerprint(checkpoint)
    previous = read_state(root)
    state = previous or {"version": 1, "files": {}, "stalled_batches": 0}
    changed_inputs, changed_artifacts = [], []
    for role, paths in (("source", sources), ("guide", guides), ("artifact", artifacts)):
        for raw in paths:
            path = (root / raw).resolve()
            digest = fingerprint(path)
            key = str(path)
            old = state["files"].get(key)
            if old and old["role"] != role:
                raise ValueError(f"File already recorded as {old['role']}: {path}")
            if not old or old["sha256"] != digest:
                (changed_artifacts if role == "artifact" else changed_inputs).append(key)
            state["files"][key] = {"role": role, "sha256": digest}
    # A different guide, stage label or next-action promise is not substantive progress.
    advanced = bool(finding.strip() or changed_artifacts)
    if previous and stage != previous["stage"] and not advanced:
        raise ValueError("Stage changes need a recorded finding or a new/changed artifact")
    state["stalled_batches"] = 0 if advanced else state["stalled_batches"] + 1
    state.update(stage=stage, next_action=next_action.strip(),
                 updated_at=datetime.now(timezone.utc).isoformat(),
                 checkpoint_sha256=fingerprint(checkpoint))
    if advanced:
        state["last_advance"] = {"at": state["updated_at"], "finding": finding.strip(),
                                 "artifacts": changed_artifacts}
    if changed_inputs:
        state["last_input_changes"] = changed_inputs
    temp = root / (STATE + ".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, root / STATE)
    return status(root)


def status(root):
    state = read_state(root)
    if state is None:
        return {"state": "not_initialized", "checkpoint_exists": (root / "research_checkpoint.md").is_file(),
                "next_action": "Inspect existing checkpoint/artifacts; reconstruct only missing progress. Do not restart analysis by default."}
    files = []
    for name, info in state["files"].items():
        try:
            condition = "unchanged" if fingerprint(Path(name)) == info["sha256"] else "changed"
        except (ValueError, OSError):
            condition = "missing_or_unreadable"
        files.append({"path": name, "role": info["role"], "condition": condition})
    try:
        checkpoint = "unchanged" if fingerprint(root / "research_checkpoint.md") == state["checkpoint_sha256"] else "changed"
    except (ValueError, OSError):
        checkpoint = "missing_or_unreadable"
    return {"stage": state["stage"], "next_action": state["next_action"],
            "checkpoint": checkpoint, "last_advance": state.get("last_advance"),
            "stalled_batches": state["stalled_batches"],
            "needs_diagnosis": state["stalled_batches"] >= 2,
            "files": files,
            "quality": "Not evaluated. Stage and findings are agent records, not acceptance proof."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "record"))
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--stage", choices=STAGES)
    parser.add_argument("--next", dest="next_action")
    parser.add_argument("--finding", default="", help="Concrete new evidence/decision with locator; also retain details in checkpoint")
    for flag in ("source", "guide", "artifact"):
        parser.add_argument("--" + flag, action="append", default=[])
    args = parser.parse_args()
    root = args.workspace.resolve()
    try:
        if args.command == "status":
            result = status(root)
        else:
            if not args.stage or not args.next_action:
                parser.error("record requires --stage and --next")
            result = record(root, args.stage, args.next_action, args.finding,
                            args.source, args.guide, args.artifact)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Workflow state error: {exc}\n")


if __name__ == "__main__":
    main()
