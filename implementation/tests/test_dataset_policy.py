import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from ipcv_attire.dataset_policy import (  # noqa: E402
    derive_targets,
    load_policy,
    require_showcase_approval,
    validate_annotation_data,
)


POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "dataset-policy.json"


class DatasetPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(POLICY_PATH)

    def test_collared_allowed_sleeve_top(self) -> None:
        targets = derive_targets(
            "shirt, blouse",
            ["shirt (collar)", "wrist-length"],
            self.policy,
        )
        self.assertTrue(targets["collared_top"])
        self.assertTrue(targets["allowed_sleeve"])
        self.assertFalse(targets["revealing_top"])

    def test_garment_part_annotations_supply_component_targets(self) -> None:
        collar = derive_targets("collar", ["shirt (collar)"], self.policy)
        sleeve = derive_targets("sleeve", ["wrist-length"], self.policy)
        neckline = derive_targets("neckline", ["round (neck)"], self.policy)
        self.assertTrue(collar["collared_top"])
        self.assertTrue(sleeve["allowed_sleeve"])
        self.assertTrue(neckline["casual_round_neck_top"])

    def test_revealing_top_is_internal_target(self) -> None:
        targets = derive_targets("top, t-shirt, sweatshirt", ["crop (top)"], self.policy)
        self.assertTrue(targets["revealing_top"])

    def test_formal_bottom_is_only_a_proxy(self) -> None:
        formal = derive_targets("pants", ["regular (fit)"], self.policy)
        cargo = derive_targets("pants", ["cargo (pants)"], self.policy)
        self.assertTrue(formal["formal_bottom_candidate"])
        self.assertFalse(cargo["formal_bottom_candidate"])
        self.assertTrue(cargo["casual_or_tight_bottom"])

    def test_annotation_graph_validation(self) -> None:
        data = {
            "images": [{"id": 1}],
            "categories": [{"id": 2}],
            "attributes": [{"id": 3}],
            "annotations": [
                {
                    "id": 4,
                    "image_id": 1,
                    "category_id": 2,
                    "attribute_ids": [3],
                    "bbox": [0, 0, 10, 10],
                }
            ],
        }
        summary = validate_annotation_data(data)
        self.assertEqual(summary["annotations"], 1)
        self.assertEqual(summary["invalid_zero_area_boxes"], 0)

    def test_zero_area_box_is_reported_as_source_noise(self) -> None:
        data = {
            "images": [{"id": 1}],
            "categories": [{"id": 2}],
            "attributes": [{"id": 3}],
            "annotations": [
                {
                    "id": 4,
                    "image_id": 1,
                    "category_id": 2,
                    "attribute_ids": [3],
                    "bbox": [0, 0, 0, 0],
                }
            ],
        }
        summary = validate_annotation_data(data)
        self.assertEqual(summary["invalid_zero_area_boxes"], 1)

    def test_unapproved_showcase_image_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "showcase.csv"
            manifest.write_text("image_id,status\n1,pending\n", encoding="utf-8")
            with self.assertRaises(PermissionError):
                require_showcase_approval(1, manifest)

    def test_approved_showcase_image_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "showcase.csv"
            with manifest.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["image_id", "status"])
                writer.writeheader()
                writer.writerow({"image_id": "1", "status": "approved"})
            require_showcase_approval(1, manifest)

    def test_policy_is_json_serializable(self) -> None:
        json.dumps(self.policy)


if __name__ == "__main__":
    unittest.main()
