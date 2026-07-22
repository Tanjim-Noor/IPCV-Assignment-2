import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from ipcv_attire.dataset_policy import (  # noqa: E402
    _assign_grouped_stratified_split,
    derive_compliance_label,
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
        jeans = derive_targets("pants", ["jeans"], self.policy)
        self.assertTrue(formal["formal_bottom_candidate"])
        self.assertFalse(cargo["formal_bottom_candidate"])
        self.assertFalse(jeans["formal_bottom_candidate"])
        self.assertTrue(cargo["casual_or_tight_bottom"])

    def test_remaining_supported_attire_targets(self) -> None:
        damaged = derive_targets("pants", ["jeans", "distressed"], self.policy)
        tights = derive_targets("tights, stockings", [], self.policy)
        footwear = derive_targets("shoe", [], self.policy)
        headwear = derive_targets("hat", [], self.policy)
        self.assertTrue(damaged["damaged_bottom"])
        self.assertTrue(tights["casual_or_tight_bottom"])
        self.assertTrue(footwear["footwear_present"])
        self.assertTrue(headwear["headwear_present"])

    def test_skorts_and_leisurewear_are_supported_targets(self) -> None:
        skort = derive_targets("shorts", ["skort"], self.policy)
        beachwear = derive_targets("shorts", ["boardshorts"], self.policy)
        self.assertTrue(skort["skort_bottom"])
        self.assertTrue(beachwear["leisurewear"])

    def test_prohibited_target_is_non_compliant(self) -> None:
        result = derive_compliance_label(
            ["collared_top", "revealing_top"], self.policy
        )
        self.assertEqual(result["compliance_label"], "non_compliant")
        self.assertEqual(result["failed_rules"], ["revealing_top"])

    def test_complete_required_evidence_is_compliant(self) -> None:
        result = derive_compliance_label(
            [
                "collared_top",
                "allowed_sleeve",
                "formal_bottom_candidate",
                "footwear_present",
            ],
            self.policy,
        )
        self.assertEqual(result["compliance_label"], "compliant")
        self.assertEqual(result["missing_required_rules"], [])

    def test_incomplete_evidence_requires_review(self) -> None:
        result = derive_compliance_label(["collared_top"], self.policy)
        self.assertEqual(result["compliance_label"], "review_required")
        self.assertIn("footwear_present", result["missing_required_rules"])

    def test_duplicate_groups_do_not_cross_splits(self) -> None:
        records = [
            {"image_id": 1, "duplicate_group": "same", "derived_targets": ["collared_top"]},
            {"image_id": 2, "duplicate_group": "same", "derived_targets": ["collared_top"]},
            {"image_id": 3, "duplicate_group": "other", "derived_targets": ["collared_top"]},
            {"image_id": 4, "duplicate_group": "third", "derived_targets": ["collared_top"]},
            {"image_id": 5, "duplicate_group": "fourth", "derived_targets": ["collared_top"]},
            {"image_id": 6, "duplicate_group": "fifth", "derived_targets": ["collared_top"]},
        ]
        assignments = _assign_grouped_stratified_split(records, 0.2, 7)
        self.assertEqual(assignments[1], assignments[2])

    def test_official_validation_is_reserved_for_locked_test(self) -> None:
        from ipcv_attire.dataset_policy import _image_records

        records = _image_records(
            {"images": [{"id": 1, "file_name": "a.jpg"}]},
            "official_validation",
            {},
            self.policy,
        )
        self.assertEqual(records[0]["final_split"], "locked_in_domain_test")

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
                require_showcase_approval(1, manifest, display_risk=False)

    def test_approved_showcase_image_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "showcase.csv"
            with manifest.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["image_id", "status"])
                writer.writeheader()
                writer.writerow({"image_id": "1", "status": "approved"})
            require_showcase_approval(1, manifest, display_risk=False)

    def test_display_risk_image_is_blocked_even_if_approved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "showcase.csv"
            manifest.write_text("image_id,status\n1,approved\n", encoding="utf-8")
            with self.assertRaises(PermissionError):
                require_showcase_approval(1, manifest, display_risk=True)

    def test_policy_is_json_serializable(self) -> None:
        json.dumps(self.policy)


if __name__ == "__main__":
    unittest.main()
