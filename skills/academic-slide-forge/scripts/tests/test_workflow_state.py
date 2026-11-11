"""Recovery and failure behavior, independent of any image API or active deck."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workflow_state import STATE, record, status


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "research_checkpoint.md").write_text("Whole-project flow; verified E1; pending E2", encoding="utf-8")
        (self.root / "source.txt").write_text("Evidence", encoding="utf-8")
        (self.root / "guide.md").write_text("Guidance", encoding="utf-8")

    def begin(self):
        return record(self.root, "analysis", "Resolve E2", "E1 supported: source.txt", sources=["source.txt"])

    def test_legacy_checkpoint_does_not_restart_or_mutate(self):
        result = status(self.root)
        self.assertTrue(result["checkpoint_exists"])
        self.assertFalse((self.root / STATE).exists())

    def test_resume_retains_next_action_and_flags_changed_and_missing(self):
        self.begin()
        original = (self.root / STATE).read_bytes()
        (self.root / "source.txt").write_text("Changed evidence", encoding="utf-8")
        result = status(self.root)
        self.assertEqual(result["next_action"], "Resolve E2")
        self.assertEqual(result["files"][0]["condition"], "changed")
        self.assertEqual(original, (self.root / STATE).read_bytes())
        (self.root / "source.txt").unlink()
        self.assertEqual(status(self.root)["files"][0]["condition"], "missing_or_unreadable")

    def test_repeated_read_and_new_guide_are_not_progress(self):
        self.begin()
        record(self.root, "analysis", "Resolve E2", sources=["source.txt"])
        result = record(self.root, "analysis", "Resolve E2", guides=["guide.md"])
        self.assertTrue(result["needs_diagnosis"])
        self.assertEqual(result["last_advance"]["finding"], "E1 supported: source.txt")

    def test_failed_record_preserves_previous_state(self):
        self.begin()
        original = (self.root / STATE).read_bytes()
        with self.assertRaises(ValueError):
            record(self.root, "sample", "Render", artifacts=["missing.pptx"])
        self.assertEqual(original, (self.root / STATE).read_bytes())
        with self.assertRaises(ValueError):
            record(self.root, "sample", "Render")
        self.assertEqual(original, (self.root / STATE).read_bytes())

    def test_real_artifact_progress_resets_stall_without_claiming_quality(self):
        self.begin()
        record(self.root, "analysis", "Resolve E2")
        (self.root / "deck_plan.json").write_text('{"pages": []}', encoding="utf-8")
        result = record(self.root, "plan", "Review page evidence", artifacts=["deck_plan.json"])
        self.assertEqual(result["stalled_batches"], 0)
        self.assertIn("Not evaluated", result["quality"])
        self.assertEqual(result["stage"], "plan")

    def test_checkpoint_change_and_loss_are_visible(self):
        self.begin()
        (self.root / "research_checkpoint.md").write_text("More evidence", encoding="utf-8")
        self.assertEqual(status(self.root)["checkpoint"], "changed")
        (self.root / "research_checkpoint.md").unlink()
        self.assertEqual(status(self.root)["checkpoint"], "missing_or_unreadable")
        with self.assertRaises(ValueError):
            record(self.root, "analysis", "Read source")

    def test_corrupt_state_is_not_silently_overwritten(self):
        (self.root / STATE).write_text("{broken", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            self.begin()
        self.assertEqual((self.root / STATE).read_text(encoding="utf-8"), "{broken")


if __name__ == "__main__":
    unittest.main()
