"""Semantic asset-contract gates that run before any image request."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_asset_plan import validate


class AssetPlanContractTests(unittest.TestCase):
    def base(self):
        return {
            "assets": [{
                "id": "mechanism", "output": "assets/mechanism.png",
                "prompt": "class-incremental replay memory illustration",
                "analysis_basis": "source method", "visual_brief": "input operation output",
                "prompt_review": "native labels carry exact values", "asset_role": "explanation",
                "generation_mode": "prompt-only", "page_ids": ["P01"],
                "project_terms": ["class-incremental", "replay memory"],
                "mechanism": {
                    "input_state": "new data arrives",
                    "operation": "retain selected evidence",
                    "output_state": "replay evidence is available",
                    "visible_relationship": "incoming cards approach bounded tray",
                    "native_layers": ["exact K=100 label"]
                },
                "reuse_policy": "single_page"
            }]
        }

    def test_valid_explanation_asset_passes(self):
        self.assertEqual([], validate(self.base()))

    def test_explanation_requires_mechanism_brief(self):
        plan = self.base()
        del plan["assets"][0]["mechanism"]
        self.assertTrue(any("needs a mechanism brief" in issue for issue in validate(plan)))

    def test_prompt_cannot_forbid_every_explanatory_mark(self):
        plan = self.base()
        plan["assets"][0]["prompt"] += " No arrows, no words, no numbers, no charts."
        self.assertTrue(any("forbids all explanatory marks" in issue for issue in validate(plan)))

    def test_prompt_only_cannot_smuggle_reference_images(self):
        plan = self.base()
        plan["assets"][0]["reference_images"] = ["reference.png"]
        self.assertTrue(any("prompt-only asset cannot carry reference_images" in issue
                            for issue in validate(plan)))

    def test_repeated_pages_need_reuse_policy(self):
        plan = self.base()
        plan["assets"][0]["page_ids"] = ["P01", "P02"]
        del plan["assets"][0]["reuse_policy"]
        self.assertTrue(any("repeated page_ids require" in issue for issue in validate(plan)))

    def strict_plan(self, count=2):
        plan = self.base()
        plan["contract"] = "asset-contract-v2"
        asset = plan["assets"][0]
        asset.update(exploration_mode="exploratory", candidate_group="P01-concepts",
                     candidate_count_required=2, user_review_required=True,
                     reference_use="research_only", reference_influence_policy="isolated_prompt_only",
                     final_role="component", native_reconstruction_required=False)
        plan["assets"] = [dict(copy.deepcopy(asset), id=f"A{i}", output=f"assets/A{i}.png",
                               composition_id=f"layout-{i}", prompt=f"{asset['prompt']} layout {i}")
                          for i in range(count)]
        return plan

    def test_strict_exploration_accepts_two_independent_candidates(self):
        self.assertEqual([], validate(self.strict_plan(), require_v2=True))

    def test_single_targeted_asset_does_not_need_alternatives(self):
        plan = self.strict_plan(1)
        plan["assets"][0].update(exploration_mode="single", candidate_count_required=1,
                                  user_review_required=False)
        del plan["assets"][0]["candidate_group"]
        self.assertEqual([], validate(plan, require_v2=True))

    def test_exploration_cannot_be_one_image_or_duplicate_layouts(self):
        self.assertTrue(any("independent candidates" in e for e in validate(self.strict_plan(1))))
        plan = self.strict_plan()
        plan["assets"][1]["composition_id"] = plan["assets"][0]["composition_id"]
        self.assertTrue(any("distinct composition_id" in e for e in validate(plan)))

    def test_duplicate_prompts_ignore_case_and_whitespace(self):
        plan = self.strict_plan()
        plan["assets"][1]["prompt"] = "  " + plan["assets"][0]["prompt"].upper().replace(" ", "  \n")
        self.assertTrue(any("duplicate prompts" in e for e in validate(plan)))

    def test_required_count_missing_or_invalid_returns_issues(self):
        for value in (None, "2", True, -1, [], {}):
            with self.subTest(value=value):
                plan = self.strict_plan()
                plan["assets"][0]["candidate_count_required"] = value
                self.assertTrue(validate(plan))
        plan = self.strict_plan()
        del plan["assets"][0]["candidate_count_required"]
        self.assertTrue(any("requires candidate_count_required" in e for e in validate(plan)))

    def test_current_contract_cannot_omit_policies_or_use_null_and_nonbool(self):
        self.assertTrue(any("contract=" in e for e in validate(self.base(), require_v2=True)))
        for field, value in (("reference_use", None), ("reference_influence_policy", None),
                             ("final_role", None), ("user_review_required", "true"),
                             ("native_reconstruction_required", 1)):
            with self.subTest(field=field):
                plan = self.strict_plan()
                plan["assets"][0][field] = value
                self.assertTrue(validate(plan))
                del plan["assets"][0][field]
                self.assertTrue(any(f"requires {field}" in e for e in validate(plan)))

    def test_prompt_only_cannot_claim_conditioning(self):
        plan = self.strict_plan()
        plan["assets"][0].update(reference_use="conditioning",
                                  reference_influence_policy="reference_conditioning_authorized")
        self.assertTrue(any("prompt-only asset" in e for e in validate(plan)))

    def test_design_reference_cannot_be_final_asset_or_component_alias(self):
        plan = self.strict_plan()
        asset = plan["assets"][0]
        asset.update(asset_role="design_reference", final_role="design_reference",
                     native_reconstruction_required=True)
        self.assertEqual([], validate(plan))
        for role in ("page_asset", "component"):
            asset["final_role"] = role
            self.assertTrue(any("design_reference" in e for e in validate(plan)))
        asset.update(final_role="design_reference", native_reconstruction_required=False)
        self.assertTrue(any("native_reconstruction_required=true" in e for e in validate(plan)))


if __name__ == "__main__":
    unittest.main()
