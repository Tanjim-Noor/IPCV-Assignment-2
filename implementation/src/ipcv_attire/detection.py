"""Classical HOG sliding-window component detection and outfit grouping."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp
from typing import Any, Iterable, Mapping

import cv2
import numpy as np
from skimage.feature import hog


BBox = tuple[int, int, int, int]


@dataclass(frozen=True)
class Detection:
    component: str
    bbox: BBox
    score: float
    source: str = "hog_linear_svm"

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "bbox": list(self.bbox),
            "score": float(self.score),
            "source": self.source,
        }


@dataclass
class OutfitGroup:
    outfit_id: str
    detections: list[Detection] = field(default_factory=list)
    ambiguous: bool = False


def bbox_iou(first: BBox, second: BBox) -> float:
    x1 = max(first[0], second[0])
    y1 = max(first[1], second[1])
    x2 = min(first[2], second[2])
    y2 = min(first[3], second[3])
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    first_area = max(0, first[2] - first[0]) * max(0, first[3] - first[1])
    second_area = max(0, second[2] - second[0]) * max(0, second[3] - second[1])
    return intersection / max(1, first_area + second_area - intersection)


def non_maximum_suppression(
    detections: Iterable[Detection], iou_threshold: float = 0.35
) -> list[Detection]:
    kept: list[Detection] = []
    for candidate in sorted(detections, key=lambda item: item.score, reverse=True):
        if all(
            candidate.component != current.component
            or bbox_iou(candidate.bbox, current.bbox) < iou_threshold
            for current in kept
        ):
            kept.append(candidate)
    return kept


def _hog_vector(image_rgb: np.ndarray, window: tuple[int, int]) -> np.ndarray:
    resized = cv2.resize(image_rgb, window, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
    return np.asarray(
        hog(
            gray,
            orientations=9,
            pixels_per_cell=(8, 8),
            cells_per_block=(2, 2),
            block_norm="L2-Hys",
            feature_vector=True,
        ),
        dtype=np.float32,
    )


@dataclass
class SlidingWindowModel:
    component: str
    estimator: Any
    window: tuple[int, int] = (64, 96)
    score_threshold: float = 0.65
    pyramid_scale: float = 1.35
    stride_fraction: float = 0.25

    def detect(self, image_rgb: np.ndarray) -> list[Detection]:
        height, width = image_rgb.shape[:2]
        detections: list[Detection] = []
        scale = 1.0
        current = image_rgb
        window_w, window_h = self.window
        while current.shape[1] >= window_w and current.shape[0] >= window_h:
            stride_x = max(8, round(window_w * self.stride_fraction))
            stride_y = max(8, round(window_h * self.stride_fraction))
            windows: list[np.ndarray] = []
            locations: list[tuple[int, int]] = []
            for y in range(0, current.shape[0] - window_h + 1, stride_y):
                for x in range(0, current.shape[1] - window_w + 1, stride_x):
                    windows.append(_hog_vector(current[y : y + window_h, x : x + window_w], self.window))
                    locations.append((x, y))
            if windows:
                matrix = np.stack(windows)
                if hasattr(self.estimator, "predict_proba"):
                    scores = self.estimator.predict_proba(matrix)[:, 1]
                else:
                    margins = np.asarray(self.estimator.decision_function(matrix))
                    scores = 1.0 / (1.0 + np.exp(-np.clip(margins, -20.0, 20.0)))
                for (x, y), score in zip(locations, scores, strict=True):
                    if score < self.score_threshold:
                        continue
                    x1, y1 = round(x * scale), round(y * scale)
                    x2 = min(width, round((x + window_w) * scale))
                    y2 = min(height, round((y + window_h) * scale))
                    detections.append(
                        Detection(self.component, (x1, y1, x2, y2), float(score))
                    )
            scale *= self.pyramid_scale
            current = cv2.resize(
                image_rgb,
                (max(1, round(width / scale)), max(1, round(height / scale))),
                interpolation=cv2.INTER_AREA,
            )
        return detections


@dataclass
class ComponentDetectorBundle:
    models: dict[str, SlidingWindowModel]
    nms_iou_threshold: float = 0.35
    maximum_detections_per_component: int = 8

    def detect(self, image_rgb: np.ndarray) -> list[Detection]:
        raw = [detection for model in self.models.values() for detection in model.detect(image_rgb)]
        suppressed = non_maximum_suppression(raw, self.nms_iou_threshold)
        limited: list[Detection] = []
        for component in sorted({item.component for item in suppressed}):
            candidates = [item for item in suppressed if item.component == component]
            limited.extend(
                sorted(candidates, key=lambda item: item.score, reverse=True)[
                    : self.maximum_detections_per_component
                ]
            )
        return sorted(limited, key=lambda item: item.score, reverse=True)


class HeuristicComponentDetector:
    """Transparent review-only fallback used before trained artifacts exist."""

    def detect(self, image_rgb: np.ndarray) -> list[Detection]:
        height, width = image_rgb.shape[:2]
        margin_x = round(width * 0.18)
        return [
            Detection(
                "upper_body",
                (margin_x, round(height * 0.12), width - margin_x, round(height * 0.58)),
                0.40,
                "geometry_fallback",
            ),
            Detection(
                "bottom_body",
                (margin_x, round(height * 0.45), width - margin_x, round(height * 0.90)),
                0.40,
                "geometry_fallback",
            ),
        ]


def group_detections(
    detections: Iterable[Detection], image_shape: tuple[int, ...]
) -> list[OutfitGroup]:
    """Associate components using horizontal centres and vertical ordering."""

    items = list(detections)
    if not items:
        return []
    width = image_shape[1]
    uppers = [item for item in items if item.component == "upper_body"]
    if not uppers:
        return [OutfitGroup("outfit-1", items, ambiguous=True)]
    groups = [OutfitGroup(f"outfit-{index + 1}", [upper]) for index, upper in enumerate(uppers)]
    for item in items:
        if item.component == "upper_body":
            continue
        centre = (item.bbox[0] + item.bbox[2]) / 2.0
        distances = [
            abs(centre - (group.detections[0].bbox[0] + group.detections[0].bbox[2]) / 2.0)
            / max(1, width)
            for group in groups
        ]
        selected = int(np.argmin(distances))
        if distances[selected] <= 0.35:
            groups[selected].detections.append(item)
        else:
            groups.append(
                OutfitGroup(f"outfit-{len(groups) + 1}", [item], ambiguous=True)
            )
    for group in groups:
        components = [item.component for item in group.detections]
        if len(components) != len(set(components)):
            group.ambiguous = True
    return groups


def detection_probability(score: float) -> float:
    """Convert an unbounded detector score when a calibrated value is unavailable."""

    if 0.0 <= score <= 1.0:
        return score
    clipped = max(-20.0, min(20.0, score))
    return 1.0 / (1.0 + exp(-clipped))
