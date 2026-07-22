"""End-to-end classical attire inference pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

import joblib
import numpy as np

from .compliance import ComplianceDecision
from .detection import (
    ComponentDetectorBundle,
    Detection,
    HeuristicComponentDetector,
    detection_probability,
    group_detections,
)
from .features import FeatureConfig, extract_handcrafted_features
from .preprocessing import InvalidImageError, PreprocessedImage, preprocess_image
from .reporting import (
    ComponentAnalysis,
    ImageDecisionReport,
    OutfitDecision,
    TargetPrediction,
    aggregate_outfit_decisions,
)
from .rubric import evaluate_rubric
from .segmentation import grabcut_segment


@dataclass
class RecognitionArtifact:
    target_id: str
    region: str
    estimator: Any
    low_threshold: float = 0.35
    high_threshold: float = 0.65
    hog_only_estimator: Any | None = None
    hog_feature_length: int = 0
    majority_class: int = 0

    def predict_probability(self, vector: np.ndarray) -> float:
        probability = self.estimator.predict_proba(vector.reshape(1, -1))[0, 1]
        return float(probability)

    def predict_hog_probability(self, vector: np.ndarray) -> float | None:
        estimator = getattr(self, "hog_only_estimator", None)
        length = int(getattr(self, "hog_feature_length", 0))
        if estimator is None or length <= 0:
            return None
        probability = estimator.predict_proba(vector[:length].reshape(1, -1))[0, 1]
        return float(probability)


class AttirePipeline:
    """Load one image, preserve stage evidence, and explain the final decision."""

    def __init__(
        self,
        policy: Mapping[str, Any],
        *,
        detector: Any,
        recognizers: Mapping[str, RecognitionArtifact] | None = None,
        feature_config: FeatureConfig | None = None,
        bundle_metadata: Mapping[str, Any] | None = None,
    ) -> None:
        self.policy = dict(policy)
        self.detector = detector
        self.recognizers = dict(recognizers or {})
        self.feature_config = feature_config or FeatureConfig()
        self.bundle_metadata = dict(bundle_metadata or {})

    @classmethod
    def review_only(cls, policy: Mapping[str, Any]) -> "AttirePipeline":
        """Construct a transparent geometry fallback for notebook smoke tests."""

        return cls(policy, detector=HeuristicComponentDetector())

    @classmethod
    def load(cls, bundle_dir: str | Path) -> "AttirePipeline":
        directory = Path(bundle_dir)
        artifact_path = directory / "bundle.joblib"
        manifest_path = directory / "manifest.json"
        if not artifact_path.is_file() or not manifest_path.is_file():
            raise FileNotFoundError(f"Incomplete model bundle: {directory}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if digest != manifest["bundle_sha256"]:
            raise ValueError("Model bundle hash does not match manifest.json")
        payload = joblib.load(artifact_path)
        if "policy_sha256" in manifest:
            policy_digest = hashlib.sha256(
                json.dumps(
                    payload["policy"], sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            ).hexdigest()
            if policy_digest != manifest["policy_sha256"]:
                raise ValueError("Bundled policy hash does not match manifest.json")
        return cls(
            payload["policy"],
            detector=payload["detector"],
            recognizers=payload["recognizers"],
            feature_config=FeatureConfig.from_mapping(payload["feature_config"]),
            bundle_metadata=manifest,
        )

    def _component_analysis(
        self,
        image_rgb: np.ndarray,
        detection: Detection,
        component_id: str,
    ) -> ComponentAnalysis:
        config = self.policy["pipeline"]
        segmentation = grabcut_segment(
            image_rgb,
            detection.bbox,
            iterations=int(config["grabcut_iterations"]),
            minimum_area_ratio=float(config["minimum_mask_area_ratio"]),
            maximum_area_ratio=float(config["maximum_mask_area_ratio"]),
        )
        x1, y1, x2, y2 = detection.bbox
        crop = image_rgb[y1:y2, x1:x2]
        crop_mask = segmentation.mask[y1:y2, x1:x2]
        predictions: list[TargetPrediction] = []
        feature_lengths: dict[str, int] = {}
        feature_vector: np.ndarray | None = None
        warnings: list[str] = []
        if segmentation.warning:
            warnings.append(segmentation.warning)
        if crop.size and segmentation.valid:
            features = extract_handcrafted_features(crop, crop_mask, self.feature_config)
            feature_lengths = features.feature_lengths
            feature_vector = features.vector
            for artifact in self.recognizers.values():
                if artifact.region != detection.component:
                    continue
                predictions.append(
                    TargetPrediction(
                        artifact.target_id,
                        artifact.predict_probability(features.vector),
                        artifact.region,
                        component_id,
                        artifact.low_threshold,
                        artifact.high_threshold,
                    )
                )
        return ComponentAnalysis(
            component_id=component_id,
            detection=detection,
            mask_area_ratio=segmentation.area_ratio,
            mask_edge_contact_ratio=segmentation.edge_contact_ratio,
            segmentation_valid=segmentation.valid,
            predictions=predictions,
            feature_lengths=feature_lengths,
            warnings=warnings,
            mask=segmentation.mask,
            feature_vector=feature_vector,
        )

    def analyze_with_stages(
        self, image: str | Path | np.ndarray
    ) -> tuple[ImageDecisionReport, PreprocessedImage]:
        timings: dict[str, float] = {}
        started = perf_counter()
        config = self.policy["pipeline"]
        prepared = preprocess_image(
            image,
            maximum_side=int(config["maximum_image_side"]),
            minimum_side=int(config["minimum_image_side"]),
        )
        timings["preprocessing"] = (perf_counter() - started) * 1000

        stage = perf_counter()
        detections = self.detector.detect(prepared.normalized_rgb)
        timings["detection"] = (perf_counter() - stage) * 1000
        groups = group_detections(detections, prepared.normalized_rgb.shape)

        stage = perf_counter()
        component_counter = 0
        outfit_reports: list[OutfitDecision] = []
        for group in groups:
            analyses: list[ComponentAnalysis] = []
            for detection in group.detections:
                component_counter += 1
                analyses.append(
                    self._component_analysis(
                        prepared.normalized_rgb,
                        detection,
                        f"component-{component_counter}",
                    )
                )
            predictions_by_target: dict[str, TargetPrediction] = {}
            for analysis in analyses:
                for prediction in analysis.predictions:
                    current = predictions_by_target.get(prediction.target_id)
                    if current is None or prediction.probability > current.probability:
                        predictions_by_target[prediction.target_id] = prediction

            for component, target in (("footwear", "footwear_present"), ("headwear", "headwear_present")):
                matches = [item for item in group.detections if item.component == component]
                trained_detector = isinstance(self.detector, ComponentDetectorBundle)
                if matches:
                    best = max(matches, key=lambda item: item.score)
                    probability = detection_probability(best.score)
                    evidence = next(
                        analysis.component_id
                        for analysis in analyses
                        if analysis.detection is best
                    )
                    predictions_by_target[target] = TargetPrediction(
                        target, probability, component, evidence
                    )
                elif trained_detector:
                    predictions_by_target[target] = TargetPrediction(
                        target, 0.0, component, None
                    )

            visible_regions = {
                analysis.detection.component
                for analysis in analyses
                if analysis.segmentation_valid
            }
            review_reasons: list[str] = []
            if group.ambiguous:
                review_reasons.append("Component-to-outfit grouping is ambiguous.")
            if isinstance(self.detector, HeuristicComponentDetector):
                review_reasons.append(
                    "Only the review-only geometry fallback is loaded; trained detector evidence is unavailable."
                )
            invalid = [analysis.component_id for analysis in analyses if not analysis.segmentation_valid]
            if invalid:
                review_reasons.append(
                    f"Segmentation quality failed for: {', '.join(invalid)}."
                )
            result = evaluate_rubric(
                predictions_by_target.values(),
                self.policy,
                visible_regions=visible_regions,
                extra_review_reasons=review_reasons,
            )
            outfit_reports.append(
                OutfitDecision(
                    outfit_id=group.outfit_id,
                    decision=result.decision,
                    rules=list(result.rules),
                    components=analyses,
                    reason=result.reason,
                    warnings=[warning for analysis in analyses for warning in analysis.warnings],
                )
            )
        timings["segmentation_features_recognition_rules"] = (perf_counter() - stage) * 1000
        decision, reason = aggregate_outfit_decisions(outfit_reports)
        timings["total"] = (perf_counter() - started) * 1000
        warnings = list(prepared.warnings)
        if not detections:
            warnings.append("No attire components were detected.")
        return (
            ImageDecisionReport(
                decision=decision,
                outfits=outfit_reports,
                reason=reason,
                timings_ms=timings,
                warnings=warnings,
                image_shape=prepared.normalized_rgb.shape,
                scale=prepared.scale,
            ),
            prepared,
        )

    def analyze(self, image: str | Path | np.ndarray) -> ImageDecisionReport:
        try:
            report, _ = self.analyze_with_stages(image)
            return report
        except InvalidImageError as exc:
            return ImageDecisionReport(
                decision=ComplianceDecision.REVIEW_REQUIRED,
                outfits=[],
                reason=str(exc),
                timings_ms={"total": 0.0},
                warnings=[str(exc)],
                image_shape=(0, 0, 0),
                scale=1.0,
            )
