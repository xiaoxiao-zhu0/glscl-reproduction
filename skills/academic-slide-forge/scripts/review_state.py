"""Bind manually inspected reviews to exact plan and file versions, not quality scores."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

TRACKING = "sha256-v1"


def clean_plan(plan):
    value = copy.deepcopy(plan)
    value.get("delivery", {}).pop("review", None)
    for page in value.get("pages", []):
        if isinstance(page, dict):
            page.pop("semantic_review", None)
            page.pop("visual_review", None)
    return value


def snapshot(plan, root, page_id=None):
    value = clean_plan(plan)
    pages = value.pop("pages")
    if page_id is not None:
        pages = [page for page in pages if page.get("id") == page_id]
        if len(pages) != 1:
            raise ValueError("Review page ID must uniquely identify a page")
    value["pages"] = pages
    paths = [value["delivery"]["artifact"]]
    for page in pages:
        for field in ("evidence", "authoring_files", "asset_paths"):
            paths.extend(page[field])
        paths.append(page["preview"])
        for unit in page["visual_units"]:
            paths.extend(unit.get("source_paths", []))
    hashes = {}
    for name in sorted(set(paths)):
        path = root / name
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError("Review requires nonempty source, asset, preview and delivery files")
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    payload = {"plan": value, "files": hashes}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def freshness_issues(plan, root):
    delivery = plan.get("delivery", {})
    if not isinstance(delivery, dict):
        return []  # Structural checker reports malformed delivery.
    tracking = delivery.get("review_tracking")
    if tracking is None:
        return []  # Legacy v2 compatibility, no freshness guarantee.
    if tracking != TRACKING:
        return ["delivery: unsupported review_tracking"]
    errors = []
    try:
        for page in plan["pages"]:
            expected = snapshot(plan, root, page["id"])
            for kind in ("semantic_review", "visual_review"):
                review = page.get(kind)
                if not isinstance(review, dict) or review.get("snapshot") != expected:
                    errors.append(f"{page['id']}: {kind} missing or stale; inspect current files again")
        review = delivery.get("review")
        if not isinstance(review, dict) or review.get("snapshot") != snapshot(plan, root):
            errors.append("delivery: review missing or stale; inspect current export again")
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        errors.append("Cannot verify review freshness: invalid plan or missing review inputs")
    return errors


def record_review(plan, root, kind, notes, page_id=None):
    if not notes.strip():
        raise ValueError("Concrete inspection observations are required")
    if plan["delivery"].get("review_tracking") != TRACKING:
        raise ValueError("Set delivery.review_tracking to sha256-v1 before reviewing")
    if kind not in ("semantic", "visual", "delivery"):
        raise ValueError("Unsupported review kind")
    if (kind == "delivery") != (page_id is None):
        raise ValueError("Page reviews need --page; delivery reviews must omit it")
    current = snapshot(plan, root, page_id)
    review = {"status": "passed", "notes": notes.strip(), "snapshot": current}
    if kind == "delivery":
        plan["delivery"]["review"] = review
    else:
        page = next(page for page in plan["pages"] if page["id"] == page_id)
        page[kind + "_review"] = review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--kind", choices=("semantic", "visual", "delivery"), required=True)
    parser.add_argument("--page")
    parser.add_argument("--notes", required=True, help="Actual inspection observations; not automatic approval")
    args = parser.parse_args()
    path = args.plan.resolve()
    try:
        plan = json.loads(path.read_text(encoding="utf-8-sig"))
        record_review(plan, path.parent, args.kind, args.notes, args.page)
        temp = path.with_name(path.name + ".review.tmp")
        temp.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        parser.error(str(exc))
    print("Recorded review version. This does not independently certify quality.")


if __name__ == "__main__":
    main()
