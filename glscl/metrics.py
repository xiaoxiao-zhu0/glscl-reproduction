"""Full-catalog evaluation; no sampled-negative ranking."""
from __future__ import annotations

import numpy as np
import torch


def ranking_metrics(recommendations, truth, ks=(10, 20)):
    result = {}
    if not truth:
        raise ValueError("Cannot evaluate a user with no ground-truth items")
    truth = set(truth)
    for k in ks:
        hits = np.asarray([int(int(i) in truth) for i in recommendations[:k]], dtype=float)
        discounts = 1.0 / np.log2(np.arange(len(hits)) + 2)
        ideal = (1.0 / np.log2(np.arange(min(k, len(truth))) + 2)).sum()
        result[f"Recall@{k}"] = float(hits.sum() / len(truth))
        result[f"NDCG@{k}"] = float((hits * discounts).sum() / ideal)
    return result


@torch.no_grad()
def evaluate(model, data, split="valid", ks=(10, 20), batch_size=128):
    model.eval()
    users, items = model()
    population = sorted(data.by_user[split])
    totals = {f"{metric}@{k}": 0.0 for metric in ("Recall", "NDCG") for k in ks}
    for start in range(0, len(population), batch_size):
        ids = population[start:start + batch_size]
        scores = users[ids] @ items.T
        for row, u in enumerate(ids):
            seen = set(data.by_user["train"].get(u, ()))
            if split == "test":
                seen.update(data.by_user["valid"].get(u, ()))
            if seen:
                scores[row, list(seen)] = -torch.inf
        values, indices = scores.topk(min(max(ks), data.n_items), dim=1)
        indices[~torch.isfinite(values)] = -1
        for u, recommendation in zip(ids, indices.cpu().numpy()):
            measured = ranking_metrics(recommendation, data.by_user[split][u], ks)
            for key in totals:
                totals[key] += measured[key]
    return {key: value / len(population) for key, value in totals.items()}
