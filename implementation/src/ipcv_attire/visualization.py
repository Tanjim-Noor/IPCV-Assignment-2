"""Report-ready overlays for detections, masks, rules, and decisions."""

from __future__ import annotations

import cv2
import numpy as np

from .reporting import ImageDecisionReport


COLOURS = {
    "upper_body": (30, 144, 255),
    "bottom_body": (50, 205, 50),
    "footwear": (255, 140, 0),
    "headwear": (186, 85, 211),
}


def draw_detections(image_rgb: np.ndarray, detections: list) -> np.ndarray:
    """Return an RGB copy with component boxes and scores."""

    canvas = image_rgb.copy()
    for detection in detections:
        colour = COLOURS.get(detection.component, (255, 255, 0))
        x1, y1, x2, y2 = detection.bbox
        cv2.rectangle(canvas, (x1, y1), (x2, y2), colour, 2)
        cv2.putText(
            canvas,
            f"{detection.component} {detection.score:.2f}",
            (x1, max(18, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            colour,
            1,
            cv2.LINE_AA,
        )
    return canvas


def draw_masks(image_rgb: np.ndarray, components: list) -> np.ndarray:
    """Return an RGB copy with auditable component masks overlaid."""

    canvas = image_rgb.copy()
    for component in components:
        if component.mask is None:
            continue
        colour = COLOURS.get(component.detection.component, (255, 255, 0))
        foreground = component.mask.astype(bool)
        tint = np.empty_like(canvas)
        tint[:] = colour
        canvas[foreground] = (
            0.65 * canvas[foreground] + 0.35 * tint[foreground]
        ).astype(np.uint8)
    return canvas


def render_report_overlay(image_rgb: np.ndarray, report: ImageDecisionReport) -> np.ndarray:
    canvas = image_rgb.copy()
    for outfit in report.outfits:
        for component in outfit.components:
            colour = COLOURS.get(component.detection.component, (255, 255, 0))
            if component.mask is not None:
                foreground = component.mask.astype(bool)
                overlay = np.zeros_like(canvas)
                overlay[:, :] = colour
                canvas[foreground] = (
                    0.65 * canvas[foreground] + 0.35 * overlay[foreground]
                ).astype(np.uint8)
            x1, y1, x2, y2 = component.detection.bbox
            cv2.rectangle(canvas, (x1, y1), (x2, y2), colour, 2)
            cv2.putText(
                canvas,
                f"{outfit.outfit_id}: {component.detection.component} {component.detection.score:.2f}",
                (x1, max(18, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                colour,
                1,
                cv2.LINE_AA,
            )
    banner = {
        "compliant": ((46, 139, 87), "APPROPRIATE"),
        "non_compliant": ((220, 20, 60), "INAPPROPRIATE"),
        "review_required": ((255, 165, 0), "REVIEW REQUIRED"),
    }[report.decision.value]
    cv2.rectangle(canvas, (0, 0), (canvas.shape[1], 42), banner[0], -1)
    cv2.putText(
        canvas,
        banner[1],
        (12, 29),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return canvas
