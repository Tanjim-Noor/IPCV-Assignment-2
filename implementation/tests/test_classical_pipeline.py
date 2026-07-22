import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from ipcv_attire.compliance import ComplianceDecision, RuleStatus  # noqa: E402
from ipcv_attire.dataset_policy import load_policy  # noqa: E402
from ipcv_attire.detection import (  # noqa: E402
    ComponentDetectorBundle,
    Detection,
    group_detections,
    non_maximum_suppression,
)
from ipcv_attire.evaluation import decode_coco_segmentation  # noqa: E402
from ipcv_attire.features import extract_handcrafted_features  # noqa: E402
from ipcv_attire.pipeline import AttirePipeline  # noqa: E402
from ipcv_attire.preprocessing import load_rgb_image, preprocess_image  # noqa: E402
from ipcv_attire.reporting import (  # noqa: E402
    OutfitDecision,
    TargetPrediction,
    aggregate_outfit_decisions,
)
from ipcv_attire.rubric import evaluate_rubric  # noqa: E402
from ipcv_attire.segmentation import dice_score, grabcut_segment, mask_iou  # noqa: E402
from ipcv_attire.training import _part_containment, select_uncertainty_thresholds  # noqa: E402


POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "dataset-policy.json"


class PreprocessingAndFeatureTests(unittest.TestCase):
    def test_grayscale_and_rgba_inputs_become_rgb(self) -> None:
        grayscale = np.arange(64 * 64, dtype=np.uint8).reshape(64, 64)
        rgba = np.zeros((64, 64, 4), dtype=np.uint8)
        rgba[:, :, 0] = 255
        rgba[:, :, 3] = 128
        self.assertEqual(load_rgb_image(grayscale).shape, (64, 64, 3))
        self.assertEqual(load_rgb_image(rgba).shape, (64, 64, 3))

    def test_preprocessing_is_deterministic_and_warns_for_tiny_input(self) -> None:
        image = np.full((16, 20, 3), 120, dtype=np.uint8)
        first = preprocess_image(image)
        second = preprocess_image(image)
        self.assertTrue(np.array_equal(first.normalized_rgb, second.normalized_rgb))
        self.assertTrue(first.warnings)

    def test_feature_vector_is_finite_and_deterministic(self) -> None:
        image = np.zeros((128, 64, 3), dtype=np.uint8)
        image[20:110, 12:52] = (200, 80, 40)
        mask = np.zeros((128, 64), dtype=np.uint8)
        mask[20:110, 12:52] = 1
        first = extract_handcrafted_features(image, mask)
        second = extract_handcrafted_features(image, mask)
        self.assertGreater(len(first.vector), 1000)
        self.assertTrue(np.isfinite(first.vector).all())
        self.assertTrue(np.array_equal(first.vector, second.vector))
        self.assertEqual(sum(first.feature_lengths.values()), len(first.vector))


class DetectionAndSegmentationTests(unittest.TestCase):
    def test_nms_removes_overlapping_component_box(self) -> None:
        detections = [
            Detection("upper_body", (0, 0, 50, 80), 0.9),
            Detection("upper_body", (2, 2, 52, 82), 0.8),
            Detection("bottom_body", (2, 2, 52, 82), 0.7),
        ]
        kept = non_maximum_suppression(detections, 0.3)
        self.assertEqual(len(kept), 2)

    def test_detector_bundle_caps_post_nms_components(self) -> None:
        class FixedModel:
            def detect(self, image_rgb):
                return [
                    Detection("upper_body", (index * 20, 0, index * 20 + 10, 10), 0.9 - index * 0.01)
                    for index in range(5)
                ]

        bundle = ComponentDetectorBundle(
            {"upper_body": FixedModel()}, maximum_detections_per_component=2
        )
        detections = bundle.detect(np.zeros((100, 120, 3), dtype=np.uint8))
        self.assertEqual(len(detections), 2)

    def test_component_grouping_supports_multiple_outfits(self) -> None:
        detections = [
            Detection("upper_body", (10, 10, 50, 80), 0.9),
            Detection("bottom_body", (12, 70, 52, 150), 0.8),
            Detection("upper_body", (150, 10, 190, 80), 0.9),
            Detection("footwear", (152, 150, 190, 190), 0.8),
        ]
        groups = group_detections(detections, (200, 220, 3))
        self.assertEqual(len(groups), 2)
        self.assertEqual(sum(len(group.detections) for group in groups), 4)

    def test_grabcut_and_mask_metrics(self) -> None:
        image = np.full((120, 100, 3), 245, dtype=np.uint8)
        image[20:100, 25:75] = (160, 30, 30)
        result = grabcut_segment(image, (15, 10, 85, 110))
        self.assertEqual(result.mask.shape, image.shape[:2])
        self.assertGreaterEqual(result.area_ratio, 0.0)
        self.assertLessEqual(result.area_ratio, 1.0)
        expected = np.zeros(image.shape[:2], dtype=np.uint8)
        expected[20:100, 25:75] = 1
        self.assertGreaterEqual(mask_iou(result.mask, expected), 0.0)
        self.assertGreaterEqual(dice_score(result.mask, expected), 0.0)

    def test_polygon_mask_decoding(self) -> None:
        polygon = [[2, 2, 8, 2, 8, 8, 2, 8]]
        mask = decode_coco_segmentation(polygon, 10, 10)
        self.assertEqual(mask.shape, (10, 10))
        self.assertGreater(mask.sum(), 0)

    def test_part_containment(self) -> None:
        self.assertEqual(_part_containment((10, 10, 20, 20), (0, 0, 30, 30)), 1.0)
        self.assertEqual(_part_containment((40, 40, 50, 50), (0, 0, 30, 30)), 0.0)


class RubricAndReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(POLICY_PATH)

    def complete_predictions(self) -> list[TargetPrediction]:
        required = set(self.policy["compliance_rules"]["required_evidence"])
        supported = {
            target
            for target, definition in self.policy["compliance_rules"]["rule_definitions"].items()
            if definition["model_supported"]
        }
        return [
            TargetPrediction(
                target,
                0.9 if target in required else 0.1,
                self.policy["compliance_rules"]["rule_definitions"][target]["region"],
                "component-1",
            )
            for target in sorted(supported)
        ]

    def test_complete_pass_is_appropriate_and_lists_unsupported_rules(self) -> None:
        result = evaluate_rubric(
            self.complete_predictions(),
            self.policy,
            visible_regions={"upper_body", "bottom_body", "footwear", "headwear"},
        )
        self.assertEqual(result.decision, ComplianceDecision.COMPLIANT)
        unsupported = [rule for rule in result.rules if rule.status is RuleStatus.UNSUPPORTED]
        self.assertEqual(len(unsupported), 5)

    def test_immediate_failure_does_not_stop_remaining_rule_reports(self) -> None:
        predictions = self.complete_predictions()
        predictions = [
            TargetPrediction(
                item.target_id,
                0.95 if item.target_id == "revealing_top" else item.probability,
                item.region,
                item.evidence_region,
            )
            for item in predictions
        ]
        result = evaluate_rubric(
            predictions,
            self.policy,
            visible_regions={"upper_body", "bottom_body", "footwear", "headwear"},
        )
        self.assertEqual(result.decision, ComplianceDecision.NON_COMPLIANT)
        self.assertEqual(len(result.rules), 15)
        self.assertTrue(any(rule.rule_id == "revealing_top" and rule.status is RuleStatus.FAIL for rule in result.rules))

    def test_uncertainty_requires_review(self) -> None:
        predictions = self.complete_predictions()
        predictions[0] = TargetPrediction(
            predictions[0].target_id,
            0.5,
            predictions[0].region,
            predictions[0].evidence_region,
        )
        result = evaluate_rubric(
            predictions,
            self.policy,
            visible_regions={"upper_body", "bottom_body", "footwear", "headwear"},
        )
        self.assertEqual(result.decision, ComplianceDecision.REVIEW_REQUIRED)

    def test_image_aggregation_is_conservative(self) -> None:
        compliant = OutfitDecision(
            "one", ComplianceDecision.COMPLIANT, [], [], "pass"
        )
        failed = OutfitDecision(
            "two", ComplianceDecision.NON_COMPLIANT, [], [], "fail"
        )
        decision, _ = aggregate_outfit_decisions([compliant, failed])
        self.assertEqual(decision, ComplianceDecision.NON_COMPLIANT)

    def test_threshold_selection_has_ordered_bounds(self) -> None:
        truth = np.array([0, 0, 0, 1, 1, 1])
        probabilities = np.array([0.05, 0.2, 0.4, 0.6, 0.8, 0.95])
        low, high = select_uncertainty_thresholds(
            truth, probabilities, minimum_coverage=0.5
        )
        self.assertLess(low, high)


class PipelineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(POLICY_PATH)

    def test_review_only_pipeline_returns_complete_structured_report(self) -> None:
        image = np.full((240, 160, 3), 240, dtype=np.uint8)
        image[30:210, 45:115] = (80, 120, 180)
        report = AttirePipeline.review_only(self.policy).analyze(image)
        payload = report.to_dict()
        self.assertEqual(report.decision, ComplianceDecision.REVIEW_REQUIRED)
        self.assertTrue(payload["outfits"])
        self.assertIn("unsupported_reasons", payload["outfits"][0])
        json.dumps(payload)

    def test_corrupt_image_returns_review_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.jpg"
            path.write_bytes(b"not an image")
            report = AttirePipeline.review_only(self.policy).analyze(path)
        self.assertEqual(report.decision, ComplianceDecision.REVIEW_REQUIRED)
        self.assertTrue(report.warnings)

    def test_no_detection_returns_review_required(self) -> None:
        class EmptyDetector:
            def detect(self, image_rgb):
                return []

        report = AttirePipeline(self.policy, detector=EmptyDetector()).analyze(
            np.full((128, 96, 3), 128, dtype=np.uint8)
        )
        self.assertEqual(report.decision, ComplianceDecision.REVIEW_REQUIRED)
        self.assertEqual(report.outfits, [])
        self.assertIn("No attire components were detected.", report.warnings)

    def test_single_and_multi_outfit_inputs_are_reported_separately(self) -> None:
        class FixedDetector:
            def __init__(self, detections):
                self.detections = detections

            def detect(self, image_rgb):
                return self.detections

        image = np.full((220, 240, 3), 235, dtype=np.uint8)
        image[20:190, 20:90] = (70, 110, 160)
        image[20:190, 150:220] = (160, 90, 70)
        single = AttirePipeline(
            self.policy,
            detector=FixedDetector([Detection("upper_body", (20, 20, 90, 120), 0.9)]),
        ).analyze(image)
        multiple = AttirePipeline(
            self.policy,
            detector=FixedDetector(
                [
                    Detection("upper_body", (20, 20, 90, 120), 0.9),
                    Detection("upper_body", (150, 20, 220, 120), 0.9),
                ]
            ),
        ).analyze(image)
        self.assertEqual(len(single.outfits), 1)
        self.assertEqual(len(multiple.outfits), 2)


class MethodConstraintTests(unittest.TestCase):
    def test_no_forbidden_deep_learning_imports_or_dnn_calls(self) -> None:
        forbidden = (
            "import torch",
            "import tensorflow",
            "import keras",
            "from transformers",
            "cv2.dnn",
            "import ultralytics",
        )
        implementation_root = SRC.parent
        violations: list[str] = []
        paths = list((implementation_root / "src").rglob("*.py")) + list(
            (implementation_root / "stages").rglob("*.ipynb")
        )
        for path in paths:
            text = path.read_text(encoding="utf-8").lower()
            violations.extend(f"{path.name}: {token}" for token in forbidden if token in text)
        self.assertEqual(violations, [])

    def test_no_deep_model_artifacts_are_tracked_in_implementation(self) -> None:
        implementation_root = SRC.parent
        forbidden_suffixes = {".pt", ".pth", ".onnx", ".h5", ".safetensors"}
        tracked_candidates = [
            path
            for root in (implementation_root / "models", implementation_root / "src")
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in forbidden_suffixes
        ]
        self.assertEqual(tracked_candidates, [])


if __name__ == "__main__":
    unittest.main()
