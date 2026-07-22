"""Reproducible classical detector and recognizer training."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

import joblib
import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .detection import ComponentDetectorBundle, SlidingWindowModel, _hog_vector, bbox_iou
from .features import FeatureConfig, extract_handcrafted_features
from .pipeline import RecognitionArtifact
from .preprocessing import environment_versions, load_rgb_image, preprocess_image


@dataclass(frozen=True)
class TrainingProfile:
    name: str
    detector_positives_per_component: int | None
    recognition_samples_per_region: int | None
    validation_samples_per_region: int | None
    hard_negative_limit: int
    random_seed: int = 20260722


PROFILES = {
    "smoke": TrainingProfile("smoke", 30, 80, 40, 30),
    "full": TrainingProfile("full", None, None, None, 2000),
}


@dataclass(frozen=True)
class GarmentSample:
    image_id: str
    image_path: Path
    component: str
    bbox: tuple[int, int, int, int]
    targets: frozenset[str]


def _json_list(value: str) -> list[Any]:
    return json.loads(value) if value else []


def _image_index(manifest_dir: Path, fashionpedia_root: Path) -> dict[str, dict[str, Any]]:
    with (manifest_dir / "fashionpedia-images.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        index: dict[str, dict[str, Any]] = {}
        for row in csv.DictReader(handle):
            row["image_path"] = fashionpedia_root / row["relative_image_path"]
            row["derived_targets"] = frozenset(_json_list(row["derived_targets"]))
            index[row["image_id"]] = row
        return index


def collect_samples(
    manifest_dir: str | Path,
    fashionpedia_root: str | Path,
    policy: Mapping[str, Any],
    *,
    split: str,
    limit_per_component: int | None = None,
) -> list[GarmentSample]:
    """Collect component boxes and associate garment-part targets to parents."""

    manifest_path = Path(manifest_dir)
    root = Path(fashionpedia_root)
    images = _image_index(manifest_path, root)
    groups = {
        component: set(names)
        for component, names in policy["pipeline"]["component_groups"].items()
    }
    parts = set(policy["categories"]["garment_parts"])
    by_image: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with (manifest_path / "fashionpedia-annotations.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        for row in csv.DictReader(handle):
            if row["final_split"] != split:
                continue
            component: str | None = next(
                (
                    name
                    for name, categories in groups.items()
                    if row["category_name"] in categories
                ),
                None,
            )
            if component is None and row["category_name"] not in parts:
                continue
            x, y, width, height = (float(value) for value in _json_list(row["bbox"]))
            row["parsed_bbox"] = (
                max(0, round(x)),
                max(0, round(y)),
                max(1, round(x + width)),
                max(1, round(y + height)),
            )
            row["component"] = component
            row["parsed_targets"] = set(_json_list(row["derived_targets"]))
            by_image[row["image_id"]].append(row)

    counts: dict[str, int] = defaultdict(int)
    samples: list[GarmentSample] = []
    for image_id in sorted(by_image, key=lambda value: int(value)):
        records = by_image[image_id]
        part_records = [record for record in records if record["category_name"] in parts]
        for record in records:
            component = record["component"]
            if component is None:
                continue
            if limit_per_component is not None and counts[component] >= limit_per_component:
                continue
            targets = set(record["parsed_targets"])
            if component == "upper_body":
                for part in part_records:
                    if _part_containment(part["parsed_bbox"], record["parsed_bbox"]) >= 0.25:
                        targets.update(part["parsed_targets"])
            image = images[image_id]
            samples.append(
                GarmentSample(
                    image_id,
                    Path(image["image_path"]),
                    component,
                    record["parsed_bbox"],
                    frozenset(targets),
                )
            )
            counts[component] += 1
    return samples


def _part_containment(
    part: tuple[int, int, int, int], parent: tuple[int, int, int, int]
) -> float:
    x1 = max(part[0], parent[0])
    y1 = max(part[1], parent[1])
    x2 = min(part[2], parent[2])
    y2 = min(part[3], parent[3])
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    part_area = max(1, (part[2] - part[0]) * (part[3] - part[1]))
    return intersection / part_area


@lru_cache(maxsize=16)
def _cached_image(path: str) -> np.ndarray:
    return load_rgb_image(path)


def _crop(image: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    height, width = image.shape[:2]
    x1, y1, x2, y2 = bbox
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(width, x2), min(height, y2)
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"Invalid crop after clipping: {bbox}")
    return image[y1:y2, x1:x2]


def _negative_crop(
    image: np.ndarray,
    positive_bbox: tuple[int, int, int, int],
    rng: np.random.Generator,
) -> np.ndarray:
    height, width = image.shape[:2]
    positive_width = max(16, positive_bbox[2] - positive_bbox[0])
    positive_height = max(16, positive_bbox[3] - positive_bbox[1])
    crop_width = min(width, positive_width)
    crop_height = min(height, positive_height)
    for _ in range(20):
        x1 = int(rng.integers(0, max(1, width - crop_width + 1)))
        y1 = int(rng.integers(0, max(1, height - crop_height + 1)))
        candidate = (x1, y1, x1 + crop_width, y1 + crop_height)
        if bbox_iou(candidate, positive_bbox) < 0.10:
            return image[y1 : y1 + crop_height, x1 : x1 + crop_width]
    corner = (0, 0, crop_width, crop_height)
    return image[corner[1] : corner[3], corner[0] : corner[2]]


def train_component_detectors(
    samples: Iterable[GarmentSample],
    *,
    random_seed: int,
    nms_iou_threshold: float,
    maximum_detections_per_component: int = 8,
    hard_negative_limit: int = 0,
) -> ComponentDetectorBundle:
    """Train one HOG linear SVM per component with deterministic negatives."""

    grouped: dict[str, list[GarmentSample]] = defaultdict(list)
    for sample in samples:
        grouped[sample.component].append(sample)
    windows = {
        "upper_body": (64, 96),
        "bottom_body": (64, 96),
        "footwear": (64, 64),
        "headwear": (64, 64),
    }
    models: dict[str, SlidingWindowModel] = {}
    rng = np.random.default_rng(random_seed)
    for component, component_samples in sorted(grouped.items()):
        vectors: list[np.ndarray] = []
        labels: list[int] = []
        for sample in component_samples:
            image = _cached_image(str(sample.image_path))
            positive = _crop(image, sample.bbox)
            negative = _negative_crop(image, sample.bbox, rng)
            vectors.extend(
                (_hog_vector(positive, windows[component]), _hog_vector(negative, windows[component]))
            )
            labels.extend((1, 0))
        if len(set(labels)) < 2:
            continue
        estimator = SGDClassifier(
            loss="hinge",
            class_weight="balanced",
            max_iter=1500,
            tol=1e-4,
            random_state=random_seed,
            average=True,
        )
        matrix = np.stack(vectors)
        target = np.asarray(labels)
        estimator.fit(matrix, target)
        hard_vectors: list[np.ndarray] = []
        if hard_negative_limit:
            for sample in component_samples[:hard_negative_limit]:
                image = _cached_image(str(sample.image_path))
                candidate = _negative_crop(image, sample.bbox, rng)
                vector = _hog_vector(candidate, windows[component])
                if float(estimator.decision_function(vector.reshape(1, -1))[0]) > 0.0:
                    hard_vectors.append(vector)
            if hard_vectors:
                matrix = np.concatenate((matrix, np.stack(hard_vectors)), axis=0)
                target = np.concatenate(
                    (target, np.zeros(len(hard_vectors), dtype=target.dtype))
                )
                estimator.fit(matrix, target)
        models[component] = SlidingWindowModel(
            component=component,
            estimator=estimator,
            window=windows[component],
        )
    return ComponentDetectorBundle(
        models, nms_iou_threshold, maximum_detections_per_component
    )


def _region_feature_matrix(
    samples: Iterable[GarmentSample],
    region: str,
    config: FeatureConfig,
    cache_path: Path | None = None,
) -> tuple[np.ndarray, list[frozenset[str]]]:
    selected = [sample for sample in samples if sample.component == region]
    if not selected:
        return np.empty((0, 0), dtype=np.float32), []

    def vector_for(sample: GarmentSample) -> np.ndarray:
        crop = _crop(_cached_image(str(sample.image_path)), sample.bbox)
        normalized = preprocess_image(
            crop, maximum_side=max(crop.shape[:2]), minimum_side=1
        ).normalized_rgb
        return extract_handcrafted_features(normalized, config=config).vector

    first = vector_for(selected[0])
    if cache_path is None:
        matrix: np.ndarray = np.empty((len(selected), len(first)), dtype=np.float32)
    else:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        matrix = np.lib.format.open_memmap(
            cache_path,
            mode="w+",
            dtype=np.float32,
            shape=(len(selected), len(first)),
        )
    matrix[0] = first
    for index, sample in enumerate(selected[1:], start=1):
        matrix[index] = vector_for(sample)
    if isinstance(matrix, np.memmap):
        matrix.flush()
    return matrix, [sample.targets for sample in selected]


def select_uncertainty_thresholds(
    truth: np.ndarray,
    probabilities: np.ndarray,
    *,
    minimum_coverage: float = 0.8,
) -> tuple[float, float]:
    """Choose low/high thresholds on internal validation only."""

    if len(truth) < 4 or len(np.unique(truth)) < 2:
        return 0.35, 0.65
    best: tuple[float, float, float, float] | None = None
    for low in np.arange(0.10, 0.50, 0.05):
        for high in np.arange(0.55, 0.95, 0.05):
            decided = (probabilities <= low) | (probabilities >= high)
            coverage = float(decided.mean())
            if coverage < minimum_coverage or not decided.any():
                continue
            predicted = (probabilities[decided] >= high).astype(int)
            score = f1_score(truth[decided], predicted, average="macro", zero_division=0)
            candidate = (score, coverage, float(low), float(high))
            if best is None or candidate[:2] > best[:2]:
                best = candidate
    return (best[2], best[3]) if best else (0.35, 0.65)


def train_recognizers(
    train_samples: list[GarmentSample],
    validation_samples: list[GarmentSample],
    policy: Mapping[str, Any],
    *,
    feature_config: FeatureConfig,
    random_seed: int,
    cache_dir: Path | None = None,
) -> dict[str, RecognitionArtifact]:
    recognizers: dict[str, RecognitionArtifact] = {}
    cells_y = feature_config.height // feature_config.hog_pixels_per_cell[0]
    cells_x = feature_config.width // feature_config.hog_pixels_per_cell[1]
    blocks_y = cells_y - feature_config.hog_cells_per_block[0] + 1
    blocks_x = cells_x - feature_config.hog_cells_per_block[1] + 1
    hog_length = (
        blocks_y
        * blocks_x
        * feature_config.hog_cells_per_block[0]
        * feature_config.hog_cells_per_block[1]
        * feature_config.hog_orientations
    )
    minimum_coverage = float(
        policy["compliance_rules"]["default_thresholds"]["minimum_decided_coverage"]
    )
    for region, targets in policy["pipeline"]["recognition_targets"].items():
        train_x, train_target_sets = _region_feature_matrix(
            train_samples,
            region,
            feature_config,
            None if cache_dir is None else cache_dir / f"train-{region}.npy",
        )
        validation_x, validation_target_sets = _region_feature_matrix(
            validation_samples,
            region,
            feature_config,
            None if cache_dir is None else cache_dir / f"validation-{region}.npy",
        )
        if not len(train_x):
            continue
        for target in targets:
            if not policy["compliance_rules"]["rule_definitions"][target]["model_supported"]:
                continue
            train_y = np.array([int(target in labels) for labels in train_target_sets])
            if len(np.unique(train_y)) < 2:
                continue
            estimator = make_pipeline(
                StandardScaler(),
                SGDClassifier(
                    loss="log_loss",
                    class_weight="balanced",
                    max_iter=2000,
                    tol=1e-4,
                    random_state=random_seed,
                    average=True,
                ),
            )
            estimator.fit(train_x, train_y)
            hog_only_estimator = make_pipeline(
                StandardScaler(),
                SGDClassifier(
                    loss="log_loss",
                    class_weight="balanced",
                    max_iter=2000,
                    tol=1e-4,
                    random_state=random_seed,
                    average=True,
                ),
            )
            hog_only_estimator.fit(train_x[:, :hog_length], train_y)
            low, high = 0.35, 0.65
            if len(validation_x):
                validation_y = np.array(
                    [int(target in labels) for labels in validation_target_sets]
                )
                probabilities = estimator.predict_proba(validation_x)[:, 1]
                low, high = select_uncertainty_thresholds(
                    validation_y,
                    probabilities,
                    minimum_coverage=minimum_coverage,
                )
            recognizers[target] = RecognitionArtifact(
                target,
                region,
                estimator,
                low,
                high,
                hog_only_estimator,
                hog_length,
                int(np.mean(train_y) >= 0.5),
            )
    return recognizers


def save_model_bundle(
    bundle_dir: str | Path,
    *,
    policy: Mapping[str, Any],
    detector: ComponentDetectorBundle,
    recognizers: Mapping[str, RecognitionArtifact],
    feature_config: FeatureConfig,
    profile: TrainingProfile,
) -> Path:
    directory = Path(bundle_dir)
    directory.mkdir(parents=True, exist_ok=True)
    artifact_path = directory / "bundle.joblib"
    payload = {
        "policy": dict(policy),
        "detector": detector,
        "recognizers": dict(recognizers),
        "feature_config": feature_config.to_dict(),
    }
    joblib.dump(payload, artifact_path, compress=3)
    manifest = {
        "pipeline_version": "classical-attire-v1",
        "policy_version": policy["policy_version"],
        "policy_sha256": hashlib.sha256(
            json.dumps(policy, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "profile": profile.name,
        "feature_config": feature_config.to_dict(),
        "trained_targets": sorted(recognizers),
        "detector_components": sorted(detector.models),
        "environment": environment_versions(),
        "bundle_sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
    }
    (directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return directory


def train_pipeline(
    *,
    manifest_dir: str | Path,
    fashionpedia_root: str | Path,
    policy: Mapping[str, Any],
    bundle_dir: str | Path,
    profile_name: str = "smoke",
) -> Path:
    profile = PROFILES[profile_name]
    collection_limit = None
    if profile.detector_positives_per_component is not None:
        collection_limit = max(
            profile.detector_positives_per_component,
            profile.recognition_samples_per_region or 0,
        )
    train_samples = collect_samples(
        manifest_dir,
        fashionpedia_root,
        policy,
        split="train",
        limit_per_component=collection_limit,
    )
    validation_samples = collect_samples(
        manifest_dir,
        fashionpedia_root,
        policy,
        split="internal_validation",
        limit_per_component=profile.validation_samples_per_region,
    )
    detector_samples: list[GarmentSample] = []
    detector_counts: dict[str, int] = defaultdict(int)
    for sample in train_samples:
        limit = profile.detector_positives_per_component
        if limit is None or detector_counts[sample.component] < limit:
            detector_samples.append(sample)
            detector_counts[sample.component] += 1
    detector = train_component_detectors(
        detector_samples,
        random_seed=profile.random_seed,
        nms_iou_threshold=float(policy["pipeline"]["nms_iou_threshold"]),
        maximum_detections_per_component=int(
            policy["pipeline"]["maximum_detections_per_component"]
        ),
        hard_negative_limit=profile.hard_negative_limit,
    )
    feature_config = FeatureConfig()
    recognizers = train_recognizers(
        train_samples,
        validation_samples,
        policy,
        feature_config=feature_config,
        random_seed=profile.random_seed,
        cache_dir=Path(manifest_dir).parent / "features" / profile.name,
    )
    return save_model_bundle(
        bundle_dir,
        policy=policy,
        detector=detector,
        recognizers=recognizers,
        feature_config=feature_config,
        profile=profile,
    )
