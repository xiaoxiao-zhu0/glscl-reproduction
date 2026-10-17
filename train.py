"""Train GLSCL, select on validation only, evaluate the selected model once."""
from __future__ import annotations

import argparse
import json
import os
import platform
import random
import time
from pathlib import Path

import numpy as np
import scipy
import torch

from glscl.data import InteractionData, LocalSimilarity
from glscl.metrics import evaluate
from glscl.model import GLSCL


ROOT = Path(__file__).resolve().parent
DEFAULTS = {
    "data_dir": "data/demo", "output_dir": "runs/demo", "seed": 2026, "device": "cpu",
    "threads": 4, "epochs": 30, "batch_size": 128, "embedding_dim": 64, "layers": 2,
    "learning_rate": 0.001, "temperature": 0.2, "epsilon": 0.1,
    "lambda_uniform": 0.1, "lambda_local": 1e-6, "lambda_reg": 1e-4,
    "alpha": 2.5, "local_user_weight": 1.0, "similarity_threshold": 0.1,
    "loss_reduction": "sum", "normalize_local": False, "include_initial": False,
    "regularization": "l2",
    "contrastive_chunk_size": 256, "similarity_block_size": 256,
    "eval_batch_size": 128, "eval_every": 1, "patience": 10, "ks": [10, 20],
}


def resolve_path(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def validate(config):
    for name in ("threads", "epochs", "batch_size", "embedding_dim", "layers", "eval_batch_size",
                 "eval_every", "patience", "contrastive_chunk_size", "similarity_block_size"):
        if not isinstance(config[name], int) or config[name] < 1:
            raise ValueError(f"{name} must be a positive integer")
    for name in ("lambda_uniform", "lambda_local", "lambda_reg", "alpha", "local_user_weight", "epsilon"):
        if config[name] < 0 or not np.isfinite(config[name]):
            raise ValueError(f"{name} must be finite and nonnegative")
    for name in ("learning_rate", "temperature"):
        if config[name] <= 0 or not np.isfinite(config[name]):
            raise ValueError(f"{name} must be finite and positive")
    if not 0 <= config["similarity_threshold"] <= 1:
        raise ValueError("similarity_threshold must be between 0 and 1")
    if config["loss_reduction"] not in ("sum", "mean"):
        raise ValueError("loss_reduction must be sum or mean")
    if config["regularization"] not in ("l2", "l2_squared"):
        raise ValueError("regularization must be l2 or l2_squared")
    if not config["ks"] or any(not isinstance(k, int) or k < 1 for k in config["ks"]):
        raise ValueError("ks must contain positive integers")


def seed_everything(seed, threads):
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True)
    return np.random.default_rng(seed)


def build_model(data, config, device):
    return GLSCL(data.n_users, data.n_items, data.graph(device),
                 embedding_dim=config["embedding_dim"], layers=config["layers"],
                 epsilon=config["epsilon"], include_initial=config["include_initial"]).to(device)


def load_checkpoint(path, data, device):
    saved = torch.load(path, map_location=device, weights_only=True)
    if saved["fingerprint"] != data.fingerprint:
        raise ValueError("Checkpoint data fingerprint mismatch: use exactly the original splits")
    model = build_model(data, saved["config"], device)
    model.load_state_dict(saved["model"])
    return model, saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/demo.json")
    for name in ("data-dir", "output-dir", "device"):
        parser.add_argument(f"--{name}")
    for name in ("epochs", "seed", "batch-size", "threads"):
        parser.add_argument(f"--{name}", type=int)
    parser.add_argument("--eval-only", type=Path, metavar="CHECKPOINT")
    args = parser.parse_args()
    supplied = json.loads(args.config.read_text(encoding="utf-8-sig"))
    if set(supplied) - set(DEFAULTS):
        raise ValueError(f"Unknown config keys: {set(supplied) - set(DEFAULTS)}")
    config = {**DEFAULTS, **supplied}
    if args.eval_only:
        saved = torch.load(args.eval_only, map_location="cpu", weights_only=True)
        config = saved["config"].copy()
    for key in ("data_dir", "output_dir", "device", "epochs", "seed", "batch_size", "threads"):
        value = getattr(args, key, None)
        if value is not None:
            config[key] = value
    validate(config)
    rng = seed_everything(config["seed"], config["threads"])
    device = torch.device(config["device"])
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; use --device cpu or install a CUDA-enabled PyTorch")
    data = InteractionData(resolve_path(config["data_dir"]))
    print("Data:", json.dumps(data.summary()), flush=True)
    if args.eval_only:
        model, saved = load_checkpoint(args.eval_only, data, device)
        print(json.dumps({"epoch": saved["epoch"],
                          "test": evaluate(model, data, "test", config["ks"], config["eval_batch_size"])}, indent=2))
        return
    output = resolve_path(config["output_dir"])
    if (output / "best.pt").exists():
        raise FileExistsError(f"Existing run {output}; specify a new --output-dir")
    output.mkdir(parents=True, exist_ok=True)
    (output / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    env = {"python": platform.python_version(), "torch": str(torch.__version__),
           "numpy": np.__version__, "scipy": scipy.__version__, "device": str(device),
           "cuda_available": torch.cuda.is_available(), "dataset": data.summary()}
    (output / "environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    model = build_model(data, config, device)
    similarity = LocalSimilarity(data.matrix, config["similarity_block_size"]) if config["lambda_local"] else None
    optimizer = torch.optim.Adam(model.parameters(), lr=config["learning_rate"])
    initial = evaluate(model, data, "valid", config["ks"], config["eval_batch_size"])
    print("Initial validation:", json.dumps(initial), flush=True)
    selection_metric = f"Recall@{max(config['ks'])}"
    best, best_epoch, stale = -float("inf"), 0, 0
    start_time = time.perf_counter()
    with (output / "history.jsonl").open("w", encoding="utf-8") as log:
        log.write(json.dumps({"epoch": 0, "valid": initial}) + "\n")
        for epoch in range(1, config["epochs"] + 1):
            model.train()
            if device.type == "cuda":
                torch.cuda.synchronize(device)
                torch.cuda.reset_peak_memory_stats(device)
            accumulated = {}
            total_samples, steps = 0, 0
            epoch_time = time.perf_counter()
            for u, p, n in data.epoch_batches(config["batch_size"], rng):
                targets = None
                if similarity is not None:
                    targets = tuple(torch.as_tensor(similarity.select(ids, kind, config["similarity_threshold"]),
                                                    dtype=torch.long, device=device)
                                    for ids, kind in ((np.unique(u), "users"), (np.unique(p), "items")))
                users, positives, negatives = [torch.as_tensor(x, dtype=torch.long, device=device) for x in (u, p, n)]
                optimizer.zero_grad(set_to_none=True)
                loss, pieces = model.objective(users, positives, negatives, config, targets)
                if not torch.isfinite(loss):
                    raise FloatingPointError(f"Nonfinite loss at epoch {epoch}, step {steps}")
                loss.backward()
                if any(parameter.grad is not None and not torch.isfinite(parameter.grad).all()
                       for parameter in model.parameters()):
                    raise FloatingPointError(f"Nonfinite gradient at epoch {epoch}, step {steps}")
                optimizer.step()
                weight = 1 if config["loss_reduction"] == "sum" else len(u)
                for key, value in pieces.items():
                    accumulated[key] = accumulated.get(key, 0.0) + float(value) * (1 if key == "l2" else weight)
                total_samples += len(u)
                steps += 1
            averaged = {key: value / (steps if key == "l2" else total_samples)
                        for key, value in accumulated.items()}
            record = {"epoch": epoch, "loss_per_interaction": averaged,
                      "seconds": time.perf_counter() - epoch_time}
            if epoch % config["eval_every"] == 0 or epoch == config["epochs"]:
                validation_start = time.perf_counter()
                record["valid"] = evaluate(model, data, "valid", config["ks"], config["eval_batch_size"])
                record["validation_seconds"] = time.perf_counter() - validation_start
                score = record["valid"][selection_metric]
                if score > best:
                    best, best_epoch, stale = score, epoch, 0
                    torch.save({"model": model.state_dict(), "config": config, "epoch": epoch,
                                "fingerprint": data.fingerprint, "valid": record["valid"],
                                "user_ids": data.user_ids, "item_ids": data.item_ids}, output / "best.pt")
                else:
                    stale += 1
            if device.type == "cuda":
                torch.cuda.synchronize(device)
                record["gpu_peak_allocated_mib"] = torch.cuda.max_memory_allocated(device) / 1024**2
                record["gpu_peak_reserved_mib"] = torch.cuda.max_memory_reserved(device) / 1024**2
            record["epoch_wall_seconds"] = time.perf_counter() - epoch_time
            log.write(json.dumps(record) + "\n")
            log.flush()
            print(json.dumps(record), flush=True)
            if stale >= config["patience"]:
                break
    model, saved = load_checkpoint(output / "best.pt", data, device)
    result = {"status": "implementation_run_not_paper_metric_reproduction", "best_epoch": best_epoch,
              "selection_metric": selection_metric, "initial_valid": initial, "valid": saved["valid"],
              "test": evaluate(model, data, "test", config["ks"], config["eval_batch_size"]),
              "elapsed_seconds": time.perf_counter() - start_time,
              "epochs_run": epoch, "dataset": data.summary()}
    (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("RESULT:", json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
