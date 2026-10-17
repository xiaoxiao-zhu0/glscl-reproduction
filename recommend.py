"""Return item IDs for an original user ID from a trained checkpoint."""
import argparse
import json

import torch

from glscl.data import InteractionData
from train import load_checkpoint, resolve_path, seed_everything


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--user", required=True, help="Original identifier, not remapped integer index")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--data-dir")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    if args.k < 1:
        parser.error("k must be positive")
    saved = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    seed_everything(saved["config"]["seed"], saved["config"]["threads"])
    data = InteractionData(resolve_path(args.data_dir or saved["config"]["data_dir"]))
    device = torch.device(args.device)
    model, _ = load_checkpoint(args.checkpoint, data, device)
    if args.user not in data.user_ids:
        parser.error("Unknown user: this model cannot infer new users without interactions/retraining")
    u = data.user_ids.index(args.user)
    model.eval()
    with torch.no_grad():
        users, items = model()
        scores = users[u] @ items.T
        seen = data.by_user["train"].get(u, set()) | data.by_user["valid"].get(u, set())
        if seen:
            scores[list(seen)] = -torch.inf
        values, ids = scores.topk(min(args.k, data.n_items))
        result = [{"item": data.item_ids[i], "score": value}
                  for i, value in zip(ids.cpu().tolist(), values.cpu().tolist()) if value != -float("inf")]
    print(json.dumps({"user": args.user, "recommendations": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
