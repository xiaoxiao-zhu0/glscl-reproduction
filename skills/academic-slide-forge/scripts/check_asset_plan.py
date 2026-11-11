#!/usr/bin/env python3
"""Validate the semantic contract of generated presentation assets.

This is deliberately a preflight check.  It cannot judge pixels, but it can
stop a prompt-only run before a generic still life is commissioned for a
mechanism page.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ASSET_ROLES = {"explanation", "decoration", "background", "design_reference"}
GENERATION_MODES = {"prompt-only", "reference-conditioned"}
REUSE_POLICIES = {"single_page", "shared_context", "cover_background", "variant_family"}
EXPLORATION_MODES = {"single", "exploratory", "batch"}
REFERENCE_USES = {"none", "research_only", "conditioning"}
REFERENCE_POLICIES = {
    "isolated_prompt_only", "reference_conditioning_authorized", "none"
}
FINAL_ROLES = {"design_reference", "component", "page_asset"}
CONTRACT = "asset-contract-v2"
CONTRACT_FIELDS = (
    "exploration_mode", "candidate_count_required", "user_review_required",
    "reference_use", "reference_influence_policy", "final_role",
    "native_reconstruction_required",
)
MECHANISM_FIELDS = (
    "input_state", "operation", "output_state", "visible_relationship", "native_layers"
)


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate(plan, require_v2=False):
    """Return human-readable contract violations for an asset plan."""
    errors = []
    if not isinstance(plan, dict):
        return ["asset plan must be an object"]
    strict = require_v2 or plan.get("contract") == CONTRACT
    if strict and plan.get("contract") != CONTRACT:
        errors.append(f"new asset plans require contract={CONTRACT}; migrate legacy plans before generation")
    assets = plan.get("assets")
    if not isinstance(assets, list) or not assets:
        return errors + ["asset plan needs a nonempty assets list"]
    ids, outputs = set(), set()
    candidate_groups = {}
    for index, asset in enumerate(assets, 1):
        label = f"asset #{index}"
        if not isinstance(asset, dict):
            errors.append(f"{label} must be an object")
            continue
        if strict:
            for field in CONTRACT_FIELDS:
                if field not in asset:
                    errors.append(f"{label}: {CONTRACT} requires {field}")
            for field in ("user_review_required", "native_reconstruction_required"):
                if field in asset and type(asset[field]) is not bool:
                    errors.append(f"{label}: {field} must be boolean")
        aid = asset.get("id")
        if not _nonempty(aid) or aid in ids:
            errors.append(f"{label} has missing or duplicate id")
        if _nonempty(aid):
            ids.add(aid)
        output = asset.get("output")
        if not _nonempty(output) or output in outputs:
            errors.append(f"{label} has missing or duplicate output")
        if _nonempty(output):
            outputs.add(output)
        for field in ("prompt", "analysis_basis", "visual_brief", "prompt_review"):
            if not _nonempty(asset.get(field)):
                errors.append(f"{label}: missing {field}")
        role = asset.get("asset_role")
        if role not in ASSET_ROLES:
            errors.append(f"{label}: asset_role must be one of {sorted(ASSET_ROLES)}")
        mode = asset.get("generation_mode")
        if mode not in GENERATION_MODES:
            errors.append(f"{label}: generation_mode must be prompt-only or reference-conditioned")
        pages = asset.get("page_ids")
        if not isinstance(pages, list) or not pages or any(not _nonempty(p) for p in pages):
            errors.append(f"{label}: page_ids must list the pages that place this asset")
        elif len(set(pages)) != len(pages):
            errors.append(f"{label}: page_ids contains duplicates")
        if isinstance(pages, list) and len(pages) > 1 and asset.get("reuse_policy") not in REUSE_POLICIES:
            errors.append(f"{label}: repeated page_ids require an explicit reuse_policy")
        if asset.get("reuse_policy") is not None and asset.get("reuse_policy") not in REUSE_POLICIES:
            errors.append(f"{label}: invalid reuse_policy")

        exploration_mode = asset.get("exploration_mode", "single")
        if exploration_mode not in EXPLORATION_MODES:
            errors.append(f"{label}: exploration_mode must be one of {sorted(EXPLORATION_MODES)}")
        candidate_group = asset.get("candidate_group")
        required = asset.get("candidate_count_required", 1)
        if exploration_mode in {"exploratory", "batch"}:
            if not _nonempty(candidate_group):
                errors.append(f"{label}: exploratory asset needs candidate_group")
            if type(required) is not int or required < 2:
                errors.append(f"{label}: exploratory asset needs candidate_count_required >= 2")
            if not _nonempty(asset.get("composition_id")):
                errors.append(f"{label}: exploratory asset needs a distinct composition_id")
            if asset.get("user_review_required") is not True:
                errors.append(f"{label}: exploratory asset must set user_review_required=true")
        elif candidate_group is not None and not _nonempty(candidate_group):
            errors.append(f"{label}: candidate_group cannot be empty")
        if strict and exploration_mode == "single" and required != 1:
            errors.append(f"{label}: single mode requires candidate_count_required=1; use exploratory mode for alternatives")
        if _nonempty(candidate_group):
            candidate_groups.setdefault(candidate_group, []).append(asset)
        if "candidate_count_required" in asset and (type(required) is not int or required < 1):
            errors.append(f"{label}: candidate_count_required must be a positive integer")
        if "composition_id" in asset and not _nonempty(asset.get("composition_id")):
            errors.append(f"{label}: composition_id must be nonempty when provided")

        reference_use = asset.get("reference_use")
        reference_policy = asset.get("reference_influence_policy")
        if (reference_use is not None or strict) and reference_use not in REFERENCE_USES:
            errors.append(f"{label}: reference_use must be one of {sorted(REFERENCE_USES)}")
        if (reference_policy is not None or strict) and reference_policy not in REFERENCE_POLICIES:
            errors.append(f"{label}: invalid reference_influence_policy")
        if mode == "prompt-only":
            if reference_use == "conditioning":
                errors.append(f"{label}: prompt-only asset cannot declare reference conditioning")
            if reference_policy is not None and reference_policy != "isolated_prompt_only":
                errors.append(f"{label}: prompt-only asset must use isolated_prompt_only policy")
        elif mode == "reference-conditioned":
            if reference_use is not None and reference_use != "conditioning":
                errors.append(f"{label}: reference-conditioned asset must declare reference_use=conditioning")
            if reference_policy is not None and reference_policy != "reference_conditioning_authorized":
                errors.append(f"{label}: reference-conditioned asset must declare authorized conditioning policy")
        final_role = asset.get("final_role")
        if (final_role is not None or strict) and final_role not in FINAL_ROLES:
            errors.append(f"{label}: final_role must be one of {sorted(FINAL_ROLES)}")
        if role == "design_reference" and final_role == "page_asset":
            errors.append(f"{label}: design_reference cannot be a final page_asset")
        if strict and role == "design_reference" and final_role != "design_reference":
            errors.append(f"{label}: whole-page design_reference must retain final_role=design_reference; declare recovered components separately")
        if role == "design_reference" and asset.get("native_reconstruction_required") is not True:
            errors.append(f"{label}: design_reference must set native_reconstruction_required=true")

        refs = asset.get("reference_images", [])
        if refs is None:
            refs = []
        if not isinstance(refs, list):
            errors.append(f"{label}: reference_images must be a list")
            refs = []
        if mode == "prompt-only" and refs:
            errors.append(f"{label}: prompt-only asset cannot carry reference_images")
        if mode == "reference-conditioned" and not refs:
            errors.append(f"{label}: reference-conditioned asset needs reference_images")

        terms = asset.get("project_terms")
        if not isinstance(terms, list) or len(terms) < 2 or any(not _nonempty(t) for t in terms):
            errors.append(f"{label}: project_terms must contain at least two project-specific terms")
        elif _nonempty(asset.get("prompt")):
            prompt = asset["prompt"].casefold()
            if not any(str(term).casefold() in prompt for term in terms):
                errors.append(f"{label}: prompt contains none of the project_terms")

        if role == "explanation":
            mechanism = asset.get("mechanism")
            if not isinstance(mechanism, dict):
                errors.append(f"{label}: explanation asset needs a mechanism brief")
            else:
                for field in MECHANISM_FIELDS:
                    value = mechanism.get(field)
                    if field == "native_layers":
                        if not isinstance(value, list) or not value or any(not _nonempty(v) for v in value):
                            errors.append(f"{label}: mechanism.native_layers must list exact native/data layers")
                    elif not _nonempty(value):
                        errors.append(f"{label}: mechanism missing {field}")
            prompt_lower = str(asset.get("prompt", "")).casefold()
            if ("no arrows" in prompt_lower and "no words" in prompt_lower
                    and "no numbers" in prompt_lower and "no charts" in prompt_lower):
                errors.append(f"{label}: mechanism prompt forbids all explanatory marks; move precision to native layers or redesign the asset")
    for group, members in candidate_groups.items():
        exploratory = [a for a in members if a.get("exploration_mode") in {"exploratory", "batch"}]
        if not exploratory:
            continue
        required_values = [a.get("candidate_count_required") for a in exploratory
                           if type(a.get("candidate_count_required")) is int
                           and a["candidate_count_required"] >= 2]
        required = max(required_values, default=2)
        if any(a.get("exploration_mode") not in {"exploratory", "batch"} for a in members):
            errors.append(f"candidate_group {group}: every member must declare exploration mode")
        if len(set(required_values)) > 1:
            errors.append(f"candidate_group {group}: candidate_count_required must agree across candidates")
        if len(members) < required:
            errors.append(f"candidate_group {group}: expected at least {required} independent candidates, found {len(members)}")
        compositions = [str(a.get("composition_id", "")) for a in members]
        if len(compositions) != len(set(compositions)):
            errors.append(f"candidate_group {group}: candidates must have distinct composition_id values")
        prompts = [" ".join(str(a.get("prompt", "")).split()).casefold() for a in members]
        if len(prompts) != len(set(prompts)):
            errors.append(f"candidate_group {group}: duplicate prompts cannot count as independent candidates")
        if any(a.get("user_review_required") is not True for a in members):
            errors.append(f"candidate_group {group}: every candidate must require user review before selection")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--require-contract-v2", action="store_true",
                        help="Require explicit candidate, reference and final-use policy for new work")
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.resolve().read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        errors = ["Cannot read a valid asset plan"]
    else:
        errors = validate(plan, require_v2=args.require_contract_v2)
    print(f"{'FAIL' if errors else 'PASS'}: {len(errors)} issue(s)")
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
