"""Train-only graphs and similarities; deterministic identifier remapping."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import torch


def read_pairs(path: Path) -> list[tuple[str, str]]:
    """Prepared files contain one user item [ignored value] per line."""
    pairs = set()
    with path.open(encoding="utf-8-sig") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            fields = line.replace(",", " ").split()
            if len(fields) not in (2, 3):
                raise ValueError(f"{path}:{line_no}: expected user item [value]")
            pairs.add((fields[0], fields[1]))
    return sorted(pairs)


class InteractionData:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        raw = {name: read_pairs(self.directory / f"{name}.txt")
               for name in ("train", "valid", "test")}
        if any(not pairs for pairs in raw.values()):
            raise ValueError("train, valid and test must all contain interactions")
        for a, b in (("train", "valid"), ("train", "test"), ("valid", "test")):
            if set(raw[a]) & set(raw[b]):
                raise ValueError(f"Data leakage: overlapping {a}/{b} interactions")
        all_pairs = sum(raw.values(), [])
        self.user_ids = sorted({u for u, _ in all_pairs})
        self.item_ids = sorted({i for _, i in all_pairs})
        self.n_users, self.n_items = len(self.user_ids), len(self.item_ids)
        users = {u: n for n, u in enumerate(self.user_ids)}
        items = {i: n for n, i in enumerate(self.item_ids)}
        self.pairs = {name: np.asarray([(users[u], items[i]) for u, i in pairs],
                                      dtype=np.int64).reshape(-1, 2)
                      for name, pairs in raw.items()}
        self.by_user = {}
        for name, pairs in self.pairs.items():
            groups = {}
            for u, i in pairs:
                groups.setdefault(int(u), set()).add(int(i))
            self.by_user[name] = groups
        rows, cols = self.pairs["train"].T
        self.matrix = sp.csr_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)),
                                    shape=(self.n_users, self.n_items))
        counts = np.diff(self.matrix.indptr)
        if np.any(counts == self.n_items):
            raise ValueError("A training user has seen all items; no BPR negative exists")
        self.dense_negative_pools = {
            int(u): np.setdiff1d(np.arange(self.n_items), self.matrix[u].indices)
            for u in np.flatnonzero(counts > self.n_items // 2)
        }
        digest = hashlib.sha256()
        for name in ("train", "valid", "test"):
            digest.update(name.encode())
            for u, i in raw[name]:
                digest.update((u + "\t" + i + "\n").encode("utf-8"))
        self.fingerprint = digest.hexdigest()

    def graph(self, device: torch.device) -> torch.Tensor:
        """D^-1/2 A D^-1/2 with no self loops; paper Eq. (1)."""
        users, items = self.pairs["train"].T
        items = items + self.n_users
        rows, cols = np.concatenate((users, items)), np.concatenate((items, users))
        n = self.n_users + self.n_items
        degrees = np.bincount(rows, minlength=n).astype(np.float32)
        inv = np.zeros(n, dtype=np.float32)
        np.power(degrees, -0.5, out=inv, where=degrees > 0)
        values = inv[rows] * inv[cols]
        return torch.sparse_coo_tensor(
            torch.from_numpy(np.stack((rows, cols))), torch.from_numpy(values), (n, n),
            check_invariants=True,
        ).coalesce().to(device)

    def epoch_batches(self, batch_size: int, rng: np.random.Generator):
        order = rng.permutation(len(self.pairs["train"]))
        train_seen = self.by_user["train"]
        for start in range(0, len(order), batch_size):
            pairs = self.pairs["train"][order[start:start + batch_size]]
            users, positive = pairs.T
            negative = rng.integers(self.n_items, size=len(users))
            for idx, u in enumerate(users):
                if u in self.dense_negative_pools:
                    negative[idx] = rng.choice(self.dense_negative_pools[u])
                else:
                    while int(negative[idx]) in train_seen[int(u)]:
                        negative[idx] = rng.integers(self.n_items)
            yield users.copy(), positive.copy(), negative

    def summary(self):
        seen_users = set(self.by_user["train"])
        seen_items = set(self.pairs["train"][:, 1].tolist())
        return {
            "users": self.n_users, "items": self.n_items,
            **{name: len(pairs) for name, pairs in self.pairs.items()},
            "cold_users": self.n_users - len(seen_users),
            "cold_items": self.n_items - len(seen_items),
            "fingerprint": self.fingerprint,
        }


class LocalSimilarity:
    """Exact Eq. (5-9) on current batch, without global quadratic matrices.

    Norms use the full TRAIN interaction vectors, never batch-only interactions.
    Sparse row blocks bound temporary storage; no approximate global top-k filter.
    """
    def __init__(self, matrix: sp.csr_matrix, block_size: int = 256):
        self.block_size = block_size
        self.users = self._normalize(matrix)
        self.items = self._normalize(matrix.T.tocsr())

    @staticmethod
    def _normalize(matrix):
        norm = np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=1)).ravel())
        inv = np.divide(1.0, norm, out=np.zeros_like(norm), where=norm > 0)
        return (sp.diags(inv) @ matrix).tocsr()

    def select(self, ids: np.ndarray, kind: str, threshold: float) -> np.ndarray:
        """Return LOCAL indices into unique batch IDs; deterministic ties."""
        if kind not in ("users", "items"):
            raise ValueError("kind must be users or items")
        ids = np.asarray(ids, dtype=np.int64)
        if len(np.unique(ids)) != len(ids):
            raise ValueError("Batch similarity expects distinct node IDs")
        if len(ids) < 2:
            return np.arange(len(ids))
        batch = getattr(self, kind)[ids]
        targets = np.arange(len(ids))
        for start in range(0, len(ids), self.block_size):
            end = min(start + self.block_size, len(ids))
            scores = (batch[start:end] @ batch.T).toarray()
            scores[np.arange(end - start), np.arange(start, end)] = -np.inf
            best = np.argmax(scores, axis=1)
            accept = scores[np.arange(end - start), best] >= threshold
            targets[start:end] = np.where(accept, best, np.arange(start, end))
        return targets
