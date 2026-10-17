"""Bounded, detached GPU trial with durable logs and completion status."""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "server-trial"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    RUN.mkdir(parents=True, exist_ok=True)
    status = {"state": "running", "started_at_utc": now(), "pid": os.getpid(),
              "gpu": "physical GPU 0 (CUDA_VISIBLE_DEVICES=0)", "steps": []}
    def save():
        temp = RUN / "status.tmp.json"
        temp.write_text(json.dumps(status, indent=2), encoding="utf-8")
        temp.replace(RUN / "status.json")
    save()
    environment = os.environ.copy()
    environment.update(CUDA_VISIBLE_DEVICES="0", PYTHONUNBUFFERED="1")
    commands = [
        ("tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
        ("gpu-smoke", [sys.executable, "-u", "train.py", "--config", "configs/demo.json",
                       "--device", "cuda", "--epochs", "1", "--output-dir", "runs/gpu-smoke"]),
        ("full-one-epoch", [sys.executable, "-u", "train.py", "--config", "configs/douban_paper_start.json",
                            "--device", "cuda", "--epochs", "1", "--output-dir", "runs/full-one-epoch"]),
    ]
    try:
        for label, command in commands:
            status["current_step"] = label
            status["step_started_at_utc"] = now()
            save()
            started = time.perf_counter()
            with (RUN / f"{label}.log").open("w", encoding="utf-8") as log:
                completed = subprocess.run(command, cwd=ROOT, env=environment, stdout=log,
                                           stderr=subprocess.STDOUT, timeout=1800)
            status["steps"].append({"name": label, "returncode": completed.returncode,
                                    "wall_seconds": time.perf_counter() - started})
            save()
            if completed.returncode:
                raise RuntimeError(f"{label} failed; see {RUN / (label + '.log')}")
        status["state"] = "complete"
    except Exception:
        status["state"] = "failed"
        status["error"] = traceback.format_exc()
    status["finished_at_utc"] = now()
    save()


if __name__ == "__main__":
    main()
