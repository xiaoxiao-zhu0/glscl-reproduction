"""Prepare disjoint per-user 7:1:2 splits; raw downloads are hash recorded."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

import numpy as np


ROOT = Path(__file__).resolve().parent
SELFREC_COMMIT = "5b0229423cb1c727e85a704d63e460368c8b9dde"


def split_pairs(pairs, output, seed=2026, max_users=None, min_interactions=10, metadata=None):
    groups = {}
    for u, i in set(pairs):
        groups.setdefault(str(u), set()).add(str(i))
    eligible = sorted(u for u in groups if len(groups[u]) >= min_interactions)
    rng = np.random.default_rng(seed)
    if max_users is not None and len(eligible) > max_users:
        eligible = sorted(rng.choice(eligible, max_users, replace=False).tolist())
    if not eligible:
        raise ValueError("No eligible users; reduce min_interactions or check input")
    split = {name: [] for name in ("train", "valid", "test")}
    for u in eligible:
        items = np.asarray(sorted(groups[u]))
        items = items[rng.permutation(len(items))]
        n_valid, n_test = max(1, int(len(items) * 0.1)), max(1, int(len(items) * 0.2))
        n_train = len(items) - n_valid - n_test
        if n_train < 1:
            raise ValueError("Each user needs >=3 interactions for three splits")
        for name, part in (("train", items[:n_train]),
                           ("valid", items[n_train:n_train + n_valid]),
                           ("test", items[n_train + n_valid:])):
            split[name].extend((u, str(i)) for i in part)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name, pairs in split.items():
        (output / f"{name}.txt").write_text(
            "".join(f"{u}\t{i}\n" for u, i in sorted(pairs)), encoding="utf-8")
    info = {"seed": seed, "split": "per-user floor 10% valid, floor 20% test; remainder train",
            "min_interactions": min_interactions, "max_users": max_users,
            "users": len(eligible), "items": len({i for pairs in split.values() for _, i in pairs}),
            "counts": {name: len(pairs) for name, pairs in split.items()},
            **(metadata or {})}
    (output / "preparation.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return info


def download_selfrec(dataset, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {"repository": "https://github.com/Coder-Yu/SELFRec", "commit": SELFREC_COMMIT, "files": []}
    for name in ("train.txt", "test.txt"):
        url = f"https://raw.githubusercontent.com/Coder-Yu/SELFRec/{SELFREC_COMMIT}/dataset/{dataset}/{name}"
        target = directory / name
        if not target.exists():
            request = urllib.request.Request(url, headers={"User-Agent": "GLSCL-independent-reproduction"})
            with urllib.request.urlopen(request, timeout=60) as response:
                content = response.read()
            target.write_bytes(content)
        content = target.read_bytes()
        manifest["files"].append({"file": name, "url": url, "bytes": len(content),
                                  "sha256": hashlib.sha256(content).hexdigest()})
    (directory / "source.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_inputs(paths, file_format="pairs", min_rating=None):
    pairs = set()
    for path in paths:
        with Path(path).open(encoding="utf-8-sig") as stream:
            for line_no, line in enumerate(stream, 1):
                fields = line.replace(",", " ").split()
                if not fields or fields[0].startswith("#"):
                    continue
                if len(fields) < 2:
                    raise ValueError(f"{path}:{line_no}: fewer than two fields")
                if file_format == "user-list":
                    pairs.update((fields[0], i) for i in fields[1:])
                else:
                    if len(fields) not in (2, 3):
                        raise ValueError(f"{path}:{line_no}: expected user item [rating]")
                    if min_rating is not None:
                        if len(fields) != 3:
                            raise ValueError("min_rating requires an explicit third rating column")
                        if float(fields[2]) < min_rating:
                            continue
                    pairs.add((fields[0], fields[1]))
    return sorted(pairs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Synthetic community dataset; NOT paper benchmark")
    demo.add_argument("--output", type=Path, default=ROOT / "data/demo")
    demo.add_argument("--seed", type=int, default=2026)
    real = commands.add_parser("douban", help="Download pinned SELFRec ratings >=4, then re-split")
    real.add_argument("--output", type=Path, default=ROOT / "data/douban-book")
    real.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/douban-book")
    real.add_argument("--max-users", type=int)
    real.add_argument("--seed", type=int, default=2026)
    custom = commands.add_parser("split", help="Prepare local Douban/Yelp/Amazon or other interactions")
    custom.add_argument("--input", type=Path, nargs="+", required=True)
    custom.add_argument("--format", choices=("pairs", "user-list"), default="pairs")
    custom.add_argument("--min-rating", type=float)
    custom.add_argument("--output", type=Path, required=True)
    custom.add_argument("--max-users", type=int)
    custom.add_argument("--min-interactions", type=int, default=10)
    custom.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if getattr(args, "max_users", None) is not None and args.max_users < 1:
        parser.error("max-users must be positive")
    if args.command == "demo":
        rng = np.random.default_rng(args.seed)
        pairs = []
        for u in range(48):
            cluster = np.arange((u % 4) * 24, (u % 4 + 1) * 24)
            preferred = rng.choice(cluster, size=14, replace=False)
            other = rng.choice(np.setdiff1d(np.arange(96), cluster), size=2, replace=False)
            pairs.extend((f"user-{u:02}", f"item-{i:02}") for i in np.r_[preferred, other])
        split_pairs(pairs, args.output, seed=args.seed, metadata={"source": "synthetic community data"})
    elif args.command == "douban":
        source = download_selfrec("douban-book", args.raw_dir)
        pairs = load_inputs([args.raw_dir / "train.txt", args.raw_dir / "test.txt"], min_rating=4)
        split_pairs(pairs, args.output, seed=args.seed, max_users=args.max_users,
                    metadata={"source": source, "min_rating": 4,
                              "warning": "Re-split union of public files; NOT the authors' unknown split."})
    else:
        if args.format == "user-list" and args.min_rating is not None:
            parser.error("user-list contains no ratings; remove --min-rating")
        split_pairs(load_inputs(args.input, args.format, args.min_rating), args.output,
                    seed=args.seed, max_users=args.max_users, min_interactions=args.min_interactions,
                    metadata={"source": [str(path.resolve()) for path in args.input],
                              "format": args.format, "min_rating": args.min_rating})


if __name__ == "__main__":
    main()
