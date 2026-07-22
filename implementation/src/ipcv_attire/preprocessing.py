"""Deterministic input loading and classical image preprocessing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


class InvalidImageError(ValueError):
    """Raised when an input cannot be converted into a usable RGB image."""


@dataclass(frozen=True)
class PreprocessedImage:
    """Images retained to explain every preprocessing stage."""

    original_rgb: np.ndarray
    resized_rgb: np.ndarray
    normalized_rgb: np.ndarray
    scale: float
    warnings: tuple[str, ...] = ()


def _array_to_rgb(value: np.ndarray) -> np.ndarray:
    array = np.asarray(value)
    if array.size == 0:
        raise InvalidImageError("The input image is empty.")
    if array.ndim == 2:
        array = np.repeat(array[:, :, None], 3, axis=2)
    if array.ndim != 3 or array.shape[2] not in {1, 3, 4}:
        raise InvalidImageError("Expected a grayscale, RGB, or RGBA image array.")
    if array.shape[2] == 1:
        array = np.repeat(array, 3, axis=2)
    if array.dtype != np.uint8:
        finite = np.nan_to_num(array.astype(np.float32), nan=0.0, posinf=255.0, neginf=0.0)
        if finite.max(initial=0.0) <= 1.0:
            finite *= 255.0
        array = np.clip(finite, 0, 255).astype(np.uint8)
    if array.shape[2] == 4:
        alpha = array[:, :, 3:4].astype(np.float32) / 255.0
        rgb = array[:, :, :3].astype(np.float32)
        array = np.clip(rgb * alpha + 255.0 * (1.0 - alpha), 0, 255).astype(np.uint8)
    return np.ascontiguousarray(array[:, :, :3])


def load_rgb_image(image: str | Path | np.ndarray) -> np.ndarray:
    """Load a path or normalize an array into EXIF-corrected RGB uint8."""

    if isinstance(image, (str, Path)):
        path = Path(image)
        if not path.is_file():
            raise InvalidImageError(f"Image file does not exist: {path}")
        try:
            with Image.open(path) as handle:
                converted = ImageOps.exif_transpose(handle).convert("RGBA")
                return _array_to_rgb(np.asarray(converted))
        except (UnidentifiedImageError, OSError) as exc:
            raise InvalidImageError(f"Cannot decode image file: {path}") from exc
    return _array_to_rgb(np.asarray(image))


def preprocess_image(
    image: str | Path | np.ndarray,
    *,
    maximum_side: int = 1024,
    minimum_side: int = 32,
    clahe_clip_limit: float = 2.0,
) -> PreprocessedImage:
    """Resize and normalize luminance with classical CLAHE."""

    original = load_rgb_image(image)
    height, width = original.shape[:2]
    warnings: list[str] = []
    if min(height, width) < minimum_side:
        warnings.append(
            f"Image is smaller than the recommended {minimum_side}-pixel minimum side."
        )
    scale = min(1.0, maximum_side / max(height, width))
    if scale < 1.0:
        resized = cv2.resize(
            original,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    else:
        resized = original.copy()

    lab = cv2.cvtColor(resized, cv2.COLOR_RGB2LAB)
    luminance, channel_a, channel_b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=(8, 8))
    normalized_l = clahe.apply(luminance)
    normalized = cv2.cvtColor(
        cv2.merge((normalized_l, channel_a, channel_b)), cv2.COLOR_LAB2RGB
    )
    return PreprocessedImage(
        original_rgb=original,
        resized_rgb=np.ascontiguousarray(resized),
        normalized_rgb=np.ascontiguousarray(normalized),
        scale=scale,
        warnings=tuple(warnings),
    )


def environment_versions() -> dict[str, str]:
    """Return package versions for experiment manifests and notebooks."""

    import PIL
    import sklearn
    import skimage

    return {
        "numpy": np.__version__,
        "opencv": cv2.__version__,
        "pillow": PIL.__version__,
        "scikit-image": skimage.__version__,
        "scikit-learn": sklearn.__version__,
    }

