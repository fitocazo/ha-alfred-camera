"""Selection regression tests that do not require a running HA instance."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location(
    "alfred_selection", Path(__file__).resolve().parents[1] / "custom_components/alfred_snapshot/selection.py"
)
selection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selection)


class SelectionTests(unittest.TestCase):
    def test_existing_entry_fallback(self):
        entry = SimpleNamespace(data={"cameras": ["old"]}, options={})
        self.assertEqual(selection.selected_cameras(entry), ["old"])

    def test_options_override_without_mutation(self):
        entry = SimpleNamespace(data={"cameras": ["old"]}, options={"cameras": ["old", "new"]})
        selected = selection.selected_cameras(entry)
        selected.append("other")
        self.assertEqual(entry.options["cameras"], ["old", "new"])
        self.assertEqual(entry.data["cameras"], ["old"])

    def test_deselection_is_respected(self):
        entry = SimpleNamespace(data={"cameras": ["old", "new"]}, options={"cameras": ["new"]})
        self.assertEqual(selection.selected_cameras(entry), ["new"])

    def test_discovery_and_missing_selected_camera(self):
        choices = selection.camera_options([{"_id": "new", "label": "New camera"}], ["old"])
        self.assertEqual(choices, [{"value": "new", "label": "New camera"}, {"value": "old", "label": "old"}])

    def test_deduplicate_and_ignore_invalid_ids(self):
        choices = selection.camera_options([{}, {"_id": None}, {"_id": ""}, {"_id": 12}, {"_id": "a"}, {"_id": "a", "label": "Camera"}], ["a"])
        self.assertEqual(choices, [{"value": "a", "label": "Camera"}])

    def test_empty_discovery_preserves_selection(self):
        self.assertEqual(selection.camera_options([], ["old"]), [{"value": "old", "label": "old"}])
