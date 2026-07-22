"""GrabCut segmentation and mask quality measurements."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .detection import BBox


@dataclass(frozen=True)
class SegmentationResult:
    mask: np.ndarray
    area_ratio: float
    edge_contact_ratio: float
    component_count: int
    valid: bool
    warning: str | None = None


def _clip_bbox(bbox: BBox, shape: tuple[int, ...]) -> BBox:
    height, width = shape[:2]
    x1 = min(max(0, bbox[0]), width - 1)
    y1 = min(max(0, bbox[1]), height - 1)
    x2 = min(max(x1 + 1, bbox[2]), width)
    y2 = min(max(y1 + 1, bbox[3]), height)
    return x1, y1, x2, y2


def grabcut_segment(
    image_rgb: np.ndarray,
    bbox: BBox,
    *,
    iterations: int = 5,
    minimum_area_ratio: float = 0.05,
    maximum_area_ratio: float = 0.95,
) -> SegmentationResult:
    """Segment a detected component using GMM/graph-cut GrabCut."""

    x1, y1, x2, y2 = _clip_bbox(bbox, image_rgb.shape)
    mask = np.zeros(image_rgb.shape[:2], dtype=np.uint8)
    rectangle = (x1, y1, x2 - x1, y2 - y1)
    background = np.zeros((1, 65), dtype=np.float64)
    foreground = np.zeros((1, 65), dtype=np.float64)
    try:
        cv2.grabCut(
            cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR),
            mask,
            rectangle,
            background,
            foreground,
            iterations,
            cv2.GC_INIT_WITH_RECT,
        )
    except cv2.error as exc:
        return SegmentationResult(
            np.zeros_like(mask), 0.0, 1.0, 0, False, f"GrabCut failed: {exc}"
        )
    binary = np.where(
        (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0
    ).astype(np.uint8)
    kernel = np.ones((3, 3), dtype=np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    crop = binary[y1:y2, x1:x2]
    count, labels, stats, _ = cv2.connectedComponentsWithStats(crop, 8)
    component_count = max(0, count - 1)
    if count > 1:
        largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        cleaned = np.zeros_like(crop)
        cleaned[labels == largest] = 1
        binary[y1:y2, x1:x2] = cleaned
        crop = cleaned
    area_ratio = float(crop.mean()) if crop.size else 0.0
    border = np.zeros_like(crop)
    if crop.size:
        border[0, :] = border[-1, :] = 1
        border[:, 0] = border[:, -1] = 1
    edge_contact = float(np.count_nonzero(crop & border)) / max(1, np.count_nonzero(border))
    valid = minimum_area_ratio <= area_ratio <= maximum_area_ratio
    warning = None if valid else f"Mask area ratio {area_ratio:.3f} is outside quality limits."
    return SegmentationResult(
        mask=binary,
        area_ratio=area_ratio,
        edge_contact_ratio=edge_contact,
        component_count=component_count,
        valid=valid,
        warning=warning,
    )


def mask_iou(first: np.ndarray, second: np.ndarray) -> float:
    first_bool = first.astype(bool)
    second_bool = second.astype(bool)
    intersection = np.count_nonzero(first_bool & second_bool)
    union = np.count_nonzero(first_bool | second_bool)
    return intersection / max(1, union)


def dice_score(first: np.ndarray, second: np.ndarray) -> float:
    first_bool = first.astype(bool)
    second_bool = second.astype(bool)
    intersection = np.count_nonzero(first_bool & second_bool)
    return 2.0 * intersection / max(1, np.count_nonzero(first_bool) + np.count_nonzero(second_bool))

