"""Handcrafted colour, texture, edge, and shape feature extraction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

import cv2
import numpy as np
from skimage.feature import hog, local_binary_pattern


@dataclass(frozen=True)
class FeatureConfig:
    """Stable dimensions and parameters for the recognition vector."""

    width: int = 64
    height: int = 128
    hog_orientations: int = 9
    hog_pixels_per_cell: tuple[int, int] = (8, 8)
    hog_cells_per_block: tuple[int, int] = (2, 2)
    lbp_points: int = 8
    lbp_radius: int = 1
    hsv_bins: tuple[int, int, int] = (8, 4, 4)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "FeatureConfig":
        if not value:
            return cls()
        data = dict(value)
        for key in ("hog_pixels_per_cell", "hog_cells_per_block", "hsv_bins"):
            if key in data:
                data[key] = tuple(data[key])
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FeatureBundle:
    """Model vector plus inspectable intermediate visual evidence."""

    vector: np.ndarray
    hog_image: np.ndarray
    lbp_image: np.ndarray
    hsv_histogram: np.ndarray
    feature_lengths: dict[str, int]


def _prepare_crop(
    image_rgb: np.ndarray,
    mask: np.ndarray | None,
    config: FeatureConfig,
) -> tuple[np.ndarray, np.ndarray]:
    resized = cv2.resize(image_rgb, (config.width, config.height), interpolation=cv2.INTER_AREA)
    if mask is None:
        resized_mask = np.ones((config.height, config.width), dtype=np.uint8)
    else:
        resized_mask = cv2.resize(
            mask.astype(np.uint8),
            (config.width, config.height),
            interpolation=cv2.INTER_NEAREST,
        )
        resized_mask = (resized_mask > 0).astype(np.uint8)
    foreground = resized.copy()
    foreground[resized_mask == 0] = 0
    return foreground, resized_mask


def extract_handcrafted_features(
    image_rgb: np.ndarray,
    mask: np.ndarray | None = None,
    config: FeatureConfig | None = None,
) -> FeatureBundle:
    """Extract HOG, uniform LBP, HSV, moments, edges, and mask shape."""

    cfg = config or FeatureConfig()
    foreground, resized_mask = _prepare_crop(image_rgb, mask, cfg)
    gray = cv2.cvtColor(foreground, cv2.COLOR_RGB2GRAY)
    hog_vector, hog_image = hog(
        gray,
        orientations=cfg.hog_orientations,
        pixels_per_cell=cfg.hog_pixels_per_cell,
        cells_per_block=cfg.hog_cells_per_block,
        block_norm="L2-Hys",
        feature_vector=True,
        visualize=True,
    )

    lbp_image = local_binary_pattern(
        gray, cfg.lbp_points, cfg.lbp_radius, method="uniform"
    )
    lbp_bins = cfg.lbp_points + 2
    lbp_hist, _ = np.histogram(
        lbp_image[resized_mask > 0],
        bins=np.arange(lbp_bins + 1),
        range=(0, lbp_bins),
        density=True,
    )
    lbp_hist = np.nan_to_num(lbp_hist, nan=0.0)

    hsv = cv2.cvtColor(foreground, cv2.COLOR_RGB2HSV)
    hsv_hist = cv2.calcHist(
        [hsv], [0, 1, 2], resized_mask, list(cfg.hsv_bins), [0, 180, 0, 256, 0, 256]
    ).flatten()
    if hsv_hist.sum() > 0:
        hsv_hist /= hsv_hist.sum()

    pixels = foreground[resized_mask > 0].astype(np.float32)
    if pixels.size:
        mean = pixels.mean(axis=0)
        std = pixels.std(axis=0)
        safe_std = np.where(std < 1e-6, 1.0, std)
        skew = (((pixels - mean) / safe_std) ** 3).mean(axis=0)
        colour_moments = np.concatenate((mean / 255.0, std / 255.0, skew))
    else:
        colour_moments = np.zeros(9, dtype=np.float32)

    edges = cv2.Canny(gray, 80, 160)
    edge_density = np.array(
        [float(np.count_nonzero(edges & (resized_mask * 255))) / max(1, resized_mask.sum())],
        dtype=np.float32,
    )
    contours, _ = cv2.findContours(
        resized_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    area_ratio = float(resized_mask.mean())
    perimeter = sum(cv2.arcLength(contour, True) for contour in contours)
    perimeter_norm = perimeter / max(1.0, 2.0 * (cfg.width + cfg.height))
    if contours:
        largest = max(contours, key=cv2.contourArea)
        x, y, width, height = cv2.boundingRect(largest)
        aspect = width / max(1.0, height)
        solidity = cv2.contourArea(largest) / max(1.0, width * height)
    else:
        aspect = 0.0
        solidity = 0.0
    shape = np.array(
        [area_ratio, perimeter_norm, aspect, solidity], dtype=np.float32
    )

    parts = {
        "hog": np.asarray(hog_vector, dtype=np.float32),
        "lbp": np.asarray(lbp_hist, dtype=np.float32),
        "hsv": np.asarray(hsv_hist, dtype=np.float32),
        "colour_moments": np.asarray(colour_moments, dtype=np.float32),
        "edge": edge_density,
        "shape": shape,
    }
    vector = np.concatenate(list(parts.values())).astype(np.float32)
    if not np.isfinite(vector).all():
        raise ValueError("Feature extraction produced a non-finite value.")
    return FeatureBundle(
        vector=vector,
        hog_image=np.asarray(hog_image, dtype=np.float32),
        lbp_image=np.asarray(lbp_image, dtype=np.float32),
        hsv_histogram=np.asarray(hsv_hist, dtype=np.float32),
        feature_lengths={name: len(values) for name, values in parts.items()},
    )

