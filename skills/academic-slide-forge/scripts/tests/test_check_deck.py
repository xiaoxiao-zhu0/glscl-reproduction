"""Behavioral fixtures: real native and raster PPTX packages, no API calls.

Test dependencies: python-pptx and Pillow. Production checker uses only stdlib.
"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_deck import check
from review_state import record_review


class DeckGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        Image.new("RGB", (160, 90), "white").save(self.root / "asset.png")
        (self.root / "source.txt").write_text("Recorded experiment and contribution", encoding="utf-8")
        (self.root / "build.py").write_text("asset = 'asset.png'", encoding="utf-8")
        # Placeholder page preview is deliberate: the gate cannot validate pixels.
        Image.new("RGB", (160, 90), "white").save(self.root / "preview.png")
        review = {"status": "passed", "notes": "Fixture review; no real visual approval claimed"}
        self.plan = {
            "schema_version": 2, "project_analysis": "Source-derived scope and evidence",
            "design_synthesis": {
                "story": "Explain this intervention and its measurement",
                "audience_priorities": "Understand the actual change",
                "visual_needs": ["Compare documented before and after"],
                "visual_language": "Aligned comparison, restrained illustration",
                "delivery_rationale": "Editable content for revision"},
            "delivery": {"stage": "final", "format": "pptx", "artifact": "deck.pptx",
                         "pptx_mode": "native", "review": copy.deepcopy(review)},
            "pages": [{
                "id": "P01", "page_role": "method", "takeaway": "局部编辑",
                "evidence": ["source.txt"], "layout_intent": "Aligned comparison",
                "visual_reason": "Expose the documented intervention",
                "visual_units": [{"role": "explanation", "production": "native",
                                  "purpose": "Explain the actual local intervention",
                                  "project_anchor": "source.txt: edit operation",
                                  "relationship": "Before to after with unchanged context",
                                  "claim_boundary": "Functional test only",
                                  "source_paths": ["source.txt"]}],
                "visual_mode": "mixed", "image_required": True, "asset_paths": ["asset.png"],
                "asset_refs": ["asset.png"], "authoring_files": ["build.py"],
                "preview": "preview.png", "visual_review": copy.deepcopy(review),
                "semantic_review": copy.deepcopy(review), "editable_text": ["局部编辑"],
                "native_objects": {"shapes": 1},
                "motion": {"requested": False, "implemented": False, "evidence": ""}}]}
        self.asset_plan = {"assets": [{
            "id": "fixture-asset", "output": "asset.png", "prompt": "fixture scene",
            "analysis_basis": "fixture source", "visual_brief": "fixture decoration",
            "prompt_review": "fixture reviewed", "asset_role": "decoration",
            "generation_mode": "prompt-only", "page_ids": ["P01"],
            "project_terms": ["fixture", "scene"]
        }]}
        (self.root / "asset_plan.json").write_text(json.dumps(self.asset_plan), encoding="utf-8")
        self.make_deck()

    def make_deck(self, native=True, tables=False, charts=False, page_number=False, diagram=False):
        deck = Presentation()
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        slide.shapes.add_picture(str(self.root / "asset.png"), 0, 0,
                                 width=deck.slide_width, height=deck.slide_height)
        if native:
            frame = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1)).text_frame
            # Exercise main title split across differently formatted runs.
            for text in ("局部", "编辑"):
                frame.paragraphs[0].add_run().text = text
        if page_number:
            slide.shapes.add_textbox(0, 0, Inches(1), Inches(1)).text = "1"
        if diagram:
            slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(3), Inches(2), Inches(1))
        if tables:
            slide.shapes.add_table(2, 2, 0, Inches(3), Inches(3), Inches(1))
        if charts:
            data = CategoryChartData()
            data.categories = ["A", "B"]
            data.add_series("Observed", (1, 2))
            slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(4), Inches(3),
                                   Inches(3), Inches(2), data)
        deck.save(self.root / "deck.pptx")

    def issues(self):
        path = self.root / "deck_plan.json"
        path.write_text(json.dumps(self.plan, ensure_ascii=False), encoding="utf-8")
        return check(path)

    def test_native_text_with_bitmap_illustration_passes(self):
        self.assertEqual([], self.issues())

    def test_full_page_raster_cannot_claim_native(self):
        self.make_deck(native=False)
        self.assertTrue(any("image-only" in e for e in self.issues()))

    def test_page_number_does_not_replace_main_native_text(self):
        self.make_deck(native=False, page_number=True)
        self.assertTrue(any("main editable text absent" in e for e in self.issues()))

    def test_actual_tables_and_charts_checked(self):
        self.plan["pages"][0]["native_objects"] = {"tables": 1, "charts": 1}
        self.assertEqual(2, sum("expected 1 native" in e for e in self.issues()))
        self.make_deck(tables=True, charts=True)
        self.assertEqual([], self.issues())

    def test_raster_sample_allowed_but_final_requires_authorization(self):
        self.make_deck(native=False)
        self.plan["delivery"].update(stage="sample", pptx_mode="raster-preview",
                                     raster_reason="Explicitly labeled visual preview")
        self.assertEqual([], self.issues())
        self.plan["delivery"]["stage"] = "final"
        self.assertTrue(any("explicit user authorization" in e for e in self.issues()))
        self.plan["delivery"]["raster_authorized"] = True
        self.plan["delivery"]["raster_reason"] = "Fixture user explicitly requests full-slide images"
        self.assertEqual([], self.issues())

    def test_generated_picture_cannot_be_evidence(self):
        self.plan["pages"][0]["visual_units"][0].update(role="evidence", production="generated")
        self.assertTrue(any("cannot be factual evidence" in e for e in self.issues()))

    def mechanism_page(self):
        page = self.plan["pages"][0]
        page.update(page_role="mechanism", mechanism_visual={
            "input_state": "输入状态", "operation": "执行替换", "output_state": "替换后的状态",
            "visible_relationship": "仅指定槽位改变", "implementation": "mixed"})
        return page

    def write_design_reference(self, nested=False):
        folder = self.root / "plans" if nested else self.root
        folder.mkdir(exist_ok=True)
        asset = self.asset_plan["assets"][0]
        asset.update(output="../asset.png" if nested else "asset.png",
                     asset_role="design_reference", final_role="design_reference",
                     native_reconstruction_required=True)
        (folder / "asset_plan.json").write_text(json.dumps(self.asset_plan), encoding="utf-8")
        self.plan["asset_plan"] = "plans/asset_plan.json" if nested else "asset_plan.json"

    def test_mechanism_generated_implementation_and_units_rejected(self):
        page = self.mechanism_page()
        page["mechanism_visual"]["implementation"] = "generated"
        self.assertTrue(any("cannot rely on generated imagery alone" in e for e in self.issues()))
        page["mechanism_visual"]["implementation"] = "mixed"
        page["visual_units"][0]["production"] = "generated"
        self.assertTrue(any("generated-only units" in e for e in self.issues()))

    def test_method_alias_with_mechanism_still_checks_native_units(self):
        page = self.mechanism_page()
        page["page_role"] = "method"
        page["visual_units"][0]["production"] = "generated"
        self.assertTrue(any("generated-only units" in e for e in self.issues()))

    def test_mechanism_needs_declared_reconstruction(self):
        page = self.mechanism_page()
        page["native_objects"] = {}
        self.assertTrue(any("native reconstruction object" in e for e in self.issues()))

    def test_fresh_mechanism_does_not_count_title_as_diagram(self):
        page = self.mechanism_page()
        self.stamp_reviews()
        self.issues()
        issues = check(self.root / "deck_plan.json", require_fresh=True)
        self.assertTrue(any("title text boxes alone" in e for e in issues))
        page["native_objects"] = {"diagram_shapes": 1}
        self.stamp_reviews()
        self.issues()
        self.assertTrue(any("expected 1 native diagram_shapes, found 0" in e for e in
                            check(self.root / "deck_plan.json", require_fresh=True)))
        self.make_deck(diagram=True)
        self.stamp_reviews()
        self.issues()
        self.assertEqual([], check(self.root / "deck_plan.json", require_fresh=True))

    def test_design_reference_cannot_be_final_even_under_renamed_path(self):
        self.write_design_reference()
        self.assertTrue(any("design_reference asset cannot" in e for e in self.issues()))
        (self.root / "renamed.png").write_bytes((self.root / "asset.png").read_bytes())
        page = self.plan["pages"][0]
        page.update(asset_paths=["renamed.png"], asset_refs=["renamed.png"])
        (self.root / "build.py").write_text("image = 'renamed.png'", encoding="utf-8")
        self.assertTrue(any("PPTX embeds a design_reference" in e for e in self.issues()))
        page.update(asset_paths=[], asset_refs=[], image_required=False)
        self.assertTrue(any("PPTX embeds a design_reference" in e for e in self.issues()))

    def test_nested_plan_resolves_asset_paths_and_hashes_from_its_folder(self):
        self.write_design_reference(nested=True)
        issues = self.issues()
        self.assertTrue(any("design_reference asset cannot" in e for e in issues))
        self.assertTrue(any("PPTX embeds a design_reference" in e for e in issues))

    def test_reference_only_allowed_in_sample_review_pages(self):
        self.write_design_reference()
        self.plan["delivery"]["stage"] = "sample"
        for role in ("sample", "design_reference"):
            self.plan["pages"][0]["page_role"] = role
            self.assertEqual([], self.issues())
        self.plan["pages"][0]["page_role"] = "method"
        self.assertTrue(any("PPTX embeds a design_reference" in e for e in self.issues()))

    def test_reused_asset_requires_page_level_reason(self):
        second = copy.deepcopy(self.plan["pages"][0])
        second["id"] = "P02"
        self.plan["pages"].append(second)
        self.assertTrue(any("placed on multiple pages" in e for e in self.issues()))
        for page in self.plan["pages"]:
            page["asset_reuse"] = {"allowed": True, "reason": "same approved opener background"}
        self.assertFalse(any("placed on multiple pages" in e for e in self.issues()))

    def test_mechanism_page_requires_visible_states(self):
        page = self.plan["pages"][0]
        page["page_role"] = "mechanism"
        self.assertTrue(any("needs mechanism_visual" in e for e in self.issues()))
        page["mechanism_visual"] = {
            "input_state": "current and replay batches",
            "operation": "select alpha before update",
            "output_state": "mixed deployment logits",
            "visible_relationship": "shared trunk branches to two heads",
            "implementation": "native"
        }
        self.assertFalse(any("mechanism_visual" in e for e in self.issues()))

    def test_decoration_allowed_on_cover_but_not_method(self):
        self.plan["pages"][0]["visual_units"][0].update(role="decoration", production="generated")
        self.plan["asset_plan"] = "asset_plan.json"
        self.assertTrue(any("decoration only" in e for e in self.issues()))
        self.plan["pages"][0]["page_role"] = "cover"
        self.assertEqual([], self.issues())

    def test_project_analysis_must_lead_to_design(self):
        del self.plan["design_synthesis"]
        self.assertTrue(any("design_synthesis" in e for e in self.issues()))

    def test_subject_without_relationship_is_insufficient(self):
        del self.plan["pages"][0]["visual_units"][0]["relationship"]
        self.assertTrue(any("missing relationship" in e for e in self.issues()))

    def test_missing_source_and_unreviewed_export_fail(self):
        (self.root / "source.txt").unlink()
        self.plan["delivery"]["review"]["status"] = "pending"
        issues = self.issues()
        self.assertTrue(any("file absent" in e for e in issues))
        self.assertTrue(any("exported artifact review" in e for e in issues))

    def test_slide_count_must_match(self):
        second = copy.deepcopy(self.plan["pages"][0])
        second["id"] = "P02"
        self.plan["pages"].append(second)
        self.assertTrue(any("slide count" in e for e in self.issues()))

    def test_legacy_plan_requires_new_review(self):
        del self.plan["schema_version"]
        self.assertTrue(any("migrate and review" in e for e in self.issues()))

    def test_malformed_pptx_returns_issue(self):
        (self.root / "deck.pptx").write_bytes(b"not a pptx")
        self.assertTrue(any("cannot inspect valid PPTX" in e for e in self.issues()))

    def test_pdf_does_not_require_native_objects(self):
        # File gate only; this deliberately does not certify PDF validity.
        (self.root / "deck.pdf").write_bytes(b"%PDF-1.4\nfixture")
        self.plan["delivery"].update(format="pdf", artifact="deck.pdf")
        del self.plan["pages"][0]["editable_text"]
        self.assertEqual([], self.issues())

    def stamp_reviews(self):
        self.plan["delivery"]["review_tracking"] = "sha256-v1"
        for kind in ("semantic", "visual"):
            record_review(self.plan, self.root, kind, "Fixture inspection only", "P01")
        record_review(self.plan, self.root, "delivery", "Fixture export inspection only")

    def test_versioned_reviews_pass_unchanged(self):
        self.stamp_reviews()
        self.assertEqual([], self.issues())
        # Recording another review must not invalidate other records.
        record_review(self.plan, self.root, "visual", "Updated inspection notes", "P01")
        self.assertEqual([], self.issues())

    def test_new_workflow_cannot_omit_tracking(self):
        self.issues()  # Write fixture plan.
        self.assertTrue(any("tracking is required" in e for e in
                            check(self.root / "deck_plan.json", require_fresh=True)))
        self.stamp_reviews()
        self.issues()
        self.assertEqual([], check(self.root / "deck_plan.json", require_fresh=True))

    def test_versioned_reviews_reject_file_changes(self):
        for filename in ("source.txt", "build.py", "asset.png", "preview.png", "deck.pptx"):
            with self.subTest(filename=filename):
                path = self.root / filename
                original = path.read_bytes()
                self.stamp_reviews()
                path.write_bytes(original + b"changed")
                self.assertTrue(any("stale" in e for e in self.issues()))
                path.write_bytes(original)

    def test_versioned_reviews_reject_plan_changes_or_missing_snapshot(self):
        self.stamp_reviews()
        self.plan["pages"][0]["takeaway"] = "A changed claim"
        self.assertTrue(any("stale" in e for e in self.issues()))
        self.stamp_reviews()
        del self.plan["pages"][0]["semantic_review"]["snapshot"]
        self.assertTrue(any("semantic_review missing or stale" in e for e in self.issues()))


if __name__ == "__main__":
    unittest.main()
