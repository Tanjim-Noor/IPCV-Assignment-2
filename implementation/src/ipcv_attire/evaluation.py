"""Locked Fashionpedia metrics for detection, segmentation, recognition, and rules."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from pycocotools import mask as coco_mask
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
)

from .detection import Detection, bbox_iou
from .pipeline import AttirePipeline
from .segmentation import dice_score, mask_iou


@dataclass(frozen=True)
class GroundTruthComponent:
    component: str
    bbox: tuple[int, int, int, int]
    segmentation: Any
    image_height: int
    image_width: int


def decode_coco_segmentation(
    segmentation: Any, height: int, width: int
) -> np.ndarray:
    """Decode polygon, compressed RLE, or uncompressed RLE annotations."""

    if isinstance(segmentation, list):
        rles = coco_mask.frPyObjects(segmentation, height, width)
        encoded = coco_mask.merge(rles)
    elif isinstance(segmentation, dict) and isinstance(segmentation.get("counts"), list):
        encoded = coco_mask.frPyObjects(segmentation, height, width)
    else:
        encoded = segmentation
    decoded = coco_mask.decode(encoded)
    if decoded.ndim == 3:
        decoded = np.any(decoded, axis=2)
    return decoded.astype(np.uint8)


def _component_lookup(policy: Mapping[str, Any]) -> dict[str, str]:
    return {
        category: component
        for component, categories in policy["pipeline"]["component_groups"].items()
        for category in categories
    }


def load_validation_ground_truth(
    annotation_path: str | Path, policy: Mapping[str, Any]
) -> dict[str, list[GroundTruthComponent]]:
    data = json.loads(Path(annotation_path).read_text(encoding="utf-8"))
    category_names = {int(item["id"]): item["name"] for item in data["categories"]}
    image_sizes = {
        int(item["id"]): (int(item["height"]), int(item["width"]))
        for item in data["images"]
    }
    lookup = _component_lookup(policy)
    output: dict[str, list[GroundTruthComponent]] = defaultdict(list)
    for annotation in data["annotations"]:
        category = category_names[int(annotation["category_id"])]
        component = lookup.get(category)
        if component is None:
            continue
        x, y, width, height = annotation["bbox"]
        image_height, image_width = image_sizes[int(annotation["image_id"])]
        output[str(annotation["image_id"])].append(
            GroundTruthComponent(
                component,
                (round(x), round(y), round(x + width), round(y + height)),
                annotation["segmentation"],
                image_height,
                image_width,
            )
        )
    return output


def _match_components(
    predictions: list[Detection],
    truth: list[GroundTruthComponent],
    iou_threshold: float = 0.5,
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    matches: list[tuple[int, int]] = []
    used_truth: set[int] = set()
    false_predictions: list[int] = []
    for prediction_index in sorted(
        range(len(predictions)), key=lambda index: predictions[index].score, reverse=True
    ):
        candidates = [
            (bbox_iou(predictions[prediction_index].bbox, item.bbox), truth_index)
            for truth_index, item in enumerate(truth)
            if truth_index not in used_truth
            and item.component == predictions[prediction_index].component
        ]
        best = max(candidates, default=(0.0, -1))
        if best[0] >= iou_threshold:
            matches.append((prediction_index, best[1]))
            used_truth.add(best[1])
        else:
            false_predictions.append(prediction_index)
    missed = [index for index in range(len(truth)) if index not in used_truth]
    return matches, false_predictions, missed


def _average_precision(scored_labels: list[tuple[float, int]], total_truth: int) -> float:
    if total_truth == 0 or not scored_labels:
        return 0.0
    ordered = sorted(scored_labels, reverse=True)
    labels = np.asarray([label for _, label in ordered], dtype=np.float64)
    true_positive = np.cumsum(labels)
    false_positive = np.cumsum(1.0 - labels)
    recall = true_positive / total_truth
    precision = true_positive / np.maximum(1.0, true_positive + false_positive)
    recall = np.concatenate(([0.0], recall, [1.0]))
    precision = np.concatenate(([0.0], precision, [0.0]))
    precision = np.maximum.accumulate(precision[::-1])[::-1]
    changes = np.where(recall[1:] != recall[:-1])[0]
    return float(np.sum((recall[changes + 1] - recall[changes]) * precision[changes + 1]))


def _centre_window_baseline(image_shape: tuple[int, ...]) -> list[Detection]:
    """Fixed geometry-only baseline independent of image pixels and labels."""

    height, width = image_shape[:2]
    relative = {
        "upper_body": (0.25, 0.08, 0.75, 0.56),
        "bottom_body": (0.25, 0.40, 0.75, 0.86),
        "footwear": (0.18, 0.75, 0.82, 0.99),
        "headwear": (0.35, 0.00, 0.65, 0.25),
    }
    return [
        Detection(
            component,
            (round(x1 * width), round(y1 * height), round(x2 * width), round(y2 * height)),
            0.5,
            "centre_window_baseline",
        )
        for component, (x1, y1, x2, y2) in relative.items()
    ]


def evaluate_locked_test(
    pipeline: AttirePipeline,
    *,
    image_manifest: str | Path,
    fashionpedia_root: str | Path,
    validation_annotations: str | Path,
    policy: Mapping[str, Any],
    maximum_images: int | None = None,
) -> dict[str, Any]:
    """Run aggregate metrics without rendering unapproved Fashionpedia images."""

    ground_truth = load_validation_ground_truth(validation_annotations, policy)
    rows: list[dict[str, str]] = []
    with Path(image_manifest).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["final_split"] == "locked_in_domain_test":
                rows.append(row)
                if maximum_images is not None and len(rows) >= maximum_images:
                    break

    tp = fp = fn = 0
    scored_labels: list[tuple[float, int]] = []
    total_truth = 0
    segmentation_iou: list[float] = []
    segmentation_dice: list[float] = []
    bbox_baseline_iou: list[float] = []
    true_decisions: list[str] = []
    predicted_decisions: list[str] = []
    target_truth: dict[str, list[int]] = defaultdict(list)
    target_prediction: dict[str, list[int]] = defaultdict(list)
    target_probability: dict[str, list[float]] = defaultdict(list)
    hog_only_prediction: dict[str, list[int]] = defaultdict(list)
    majority_prediction: dict[str, list[int]] = defaultdict(list)
    target_coverage: dict[str, list[int]] = defaultdict(list)
    detection_cases: list[tuple[list[Detection], list[GroundTruthComponent]]] = []
    baseline_tp = baseline_fp = baseline_fn = 0
    reason_correctness: list[bool] = []
    root = Path(fashionpedia_root)

    for row in rows:
        image_path = root / row["relative_image_path"]
        report, prepared = pipeline.analyze_with_stages(image_path)
        predicted_components = [
            component
            for outfit in report.outfits
            for component in outfit.components
        ]
        predictions = [component.detection for component in predicted_components]
        truth = ground_truth.get(row["image_id"], [])
        detection_cases.append((predictions, truth))
        matches, false_predictions, missed = _match_components(predictions, truth)
        tp += len(matches)
        fp += len(false_predictions)
        fn += len(missed)
        total_truth += len(truth)
        matched_prediction_ids = {prediction_index for prediction_index, _ in matches}
        scored_labels.extend(
            (prediction.score, int(index in matched_prediction_ids))
            for index, prediction in enumerate(predictions)
        )
        baseline_matches, baseline_false, baseline_missed = _match_components(
            _centre_window_baseline(prepared.normalized_rgb.shape), truth
        )
        baseline_tp += len(baseline_matches)
        baseline_fp += len(baseline_false)
        baseline_fn += len(baseline_missed)
        for prediction_index, truth_index in matches:
            component = predicted_components[prediction_index]
            annotation = truth[truth_index]
            if component.mask is None:
                continue
            expected = decode_coco_segmentation(
                annotation.segmentation,
                annotation.image_height,
                annotation.image_width,
            )
            predicted_mask = component.mask
            if predicted_mask.shape != expected.shape:
                import cv2

                predicted_mask = cv2.resize(
                    predicted_mask,
                    (expected.shape[1], expected.shape[0]),
                    interpolation=cv2.INTER_NEAREST,
                )
            segmentation_iou.append(mask_iou(predicted_mask, expected))
            segmentation_dice.append(dice_score(predicted_mask, expected))
            x1, y1, x2, y2 = annotation.bbox
            rectangle = np.zeros_like(expected)
            rectangle[max(0, y1) : y2, max(0, x1) : x2] = 1
            bbox_baseline_iou.append(mask_iou(rectangle, expected))

        true_decisions.append(row["compliance_label"])
        predicted_decisions.append(report.decision.value)
        true_targets = set(json.loads(row["derived_targets"]))
        probabilities: dict[str, float] = {}
        hog_probabilities: dict[str, float] = {}
        for outfit in report.outfits:
            for component in outfit.components:
                for prediction in component.predictions:
                    probabilities[prediction.target_id] = max(
                        probabilities.get(prediction.target_id, 0.0),
                        prediction.probability,
                    )
                if component.feature_vector is not None:
                    for target, artifact in pipeline.recognizers.items():
                        if artifact.region != component.detection.component:
                            continue
                        probability = artifact.predict_hog_probability(
                            component.feature_vector
                        )
                        if probability is not None:
                            hog_probabilities[target] = max(
                                hog_probabilities.get(target, 0.0), probability
                            )
        for target in policy["derived_targets"]:
            if not policy["compliance_rules"]["rule_definitions"][target]["model_supported"]:
                continue
            target_truth[target].append(int(target in true_targets))
            if target in probabilities:
                target_prediction[target].append(int(probabilities[target] >= 0.5))
                target_probability[target].append(probabilities[target])
                target_coverage[target].append(1)
            else:
                target_prediction[target].append(0)
                target_probability[target].append(0.0)
                target_coverage[target].append(0)
            hog_only_prediction[target].append(
                int(hog_probabilities.get(target, 0.0) >= 0.5)
            )
            artifact = pipeline.recognizers.get(target)
            majority_prediction[target].append(
                int(getattr(artifact, "majority_class", 0)) if artifact else 0
            )
        expected_failures = set(json.loads(row["failed_rules"]))
        predicted_failures = {
            rule.rule_id
            for outfit in report.outfits
            for rule in outfit.rules
            if rule.status.value == "fail"
        }
        supported_expected = {
            target
            for target in expected_failures
            if policy["compliance_rules"]["rule_definitions"][target]["model_supported"]
        }
        reason_correctness.append(predicted_failures == supported_expected)

    labels = ["compliant", "non_compliant", "review_required"]
    recognition = {}
    for target, truth_values in target_truth.items():
        predicted_values = target_prediction[target]
        recognition[target] = {
            "f1": f1_score(truth_values, predicted_values, zero_division=0),
            "balanced_accuracy": balanced_accuracy_score(truth_values, predicted_values),
            "pr_auc": average_precision_score(
                truth_values, target_probability[target]
            ) if len(set(truth_values)) > 1 else 0.0,
            "coverage": float(np.mean(target_coverage[target])),
            "majority_baseline_f1": f1_score(
                truth_values, majority_prediction[target], zero_division=0
            ),
            "hog_only_baseline_f1": f1_score(
                truth_values, hog_only_prediction[target], zero_division=0
            ),
        }
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    decided = [value != "review_required" for value in predicted_decisions]
    decided_indices = [index for index, value in enumerate(decided) if value]
    ap_by_iou: dict[str, float] = {}
    for threshold in np.arange(0.50, 1.00, 0.05):
        threshold_scores: list[tuple[float, int]] = []
        for case_predictions, case_truth in detection_cases:
            case_matches, _, _ = _match_components(
                case_predictions, case_truth, float(threshold)
            )
            matched = {prediction_index for prediction_index, _ in case_matches}
            threshold_scores.extend(
                (prediction.score, int(index in matched))
                for index, prediction in enumerate(case_predictions)
            )
        ap_by_iou[f"{threshold:.2f}"] = _average_precision(
            threshold_scores, total_truth
        )
    return {
        "evaluated_images": len(rows),
        "detection": {
            "precision_at_iou_0_5": precision,
            "recall_at_iou_0_5": recall,
            "ap50": _average_precision(scored_labels, total_truth),
            "ap_50_to_95": float(np.mean(list(ap_by_iou.values()))) if ap_by_iou else 0.0,
            "ap_by_iou": ap_by_iou,
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "centre_window_baseline": {
                "precision_at_iou_0_5": baseline_tp / max(1, baseline_tp + baseline_fp),
                "recall_at_iou_0_5": baseline_tp / max(1, baseline_tp + baseline_fn),
            },
        },
        "segmentation": {
            "mean_iou": float(np.mean(segmentation_iou)) if segmentation_iou else 0.0,
            "mean_dice": float(np.mean(segmentation_dice)) if segmentation_dice else 0.0,
            "bbox_mask_baseline_mean_iou": float(np.mean(bbox_baseline_iou))
            if bbox_baseline_iou
            else 0.0,
            "matched_masks": len(segmentation_iou),
        },
        "recognition": recognition,
        "recognition_summary": {
            "macro_f1": float(np.mean([item["f1"] for item in recognition.values()]))
            if recognition
            else 0.0,
            "macro_balanced_accuracy": float(
                np.mean([item["balanced_accuracy"] for item in recognition.values()])
            )
            if recognition
            else 0.0,
            "macro_pr_auc": float(
                np.mean([item["pr_auc"] for item in recognition.values()])
            )
            if recognition
            else 0.0,
        },
        "compliance": {
            "macro_f1_all": f1_score(
                true_decisions,
                predicted_decisions,
                labels=labels,
                average="macro",
                zero_division=0,
            ),
            "balanced_accuracy_all": balanced_accuracy_score(
                true_decisions, predicted_decisions
            ),
            "review_rate": float(np.mean([not value for value in decided])),
            "decided_coverage": float(np.mean(decided)),
            "decided_case_macro_f1": f1_score(
                [true_decisions[index] for index in decided_indices],
                [predicted_decisions[index] for index in decided_indices],
                average="macro",
                zero_division=0,
            )
            if decided_indices
            else 0.0,
            "decided_case_accuracy": accuracy_score(
                [true_decisions[index] for index in decided_indices],
                [predicted_decisions[index] for index in decided_indices],
            ) if decided_indices else 0.0,
            "reason_exact_match": float(np.mean(reason_correctness))
            if reason_correctness
            else 0.0,
            "confusion_matrix_labels": labels,
            "confusion_matrix": confusion_matrix(
                true_decisions, predicted_decisions, labels=labels
            ).tolist(),
        },
    }
