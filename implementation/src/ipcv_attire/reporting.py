"""Serializable evidence records returned by end-to-end inference."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from .compliance import ComplianceDecision, RuleResult
from .detection import Detection


@dataclass(frozen=True)
class TargetPrediction:
    target_id: str
    probability: float
    region: str
    evidence_region: str | None
    low_threshold: float = 0.35
    high_threshold: float = 0.65


@dataclass
class ComponentAnalysis:
    component_id: str
    detection: Detection
    mask_area_ratio: float
    mask_edge_contact_ratio: float
    segmentation_valid: bool
    predictions: list[TargetPrediction] = field(default_factory=list)
    feature_lengths: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    mask: np.ndarray | None = field(default=None, repr=False, compare=False)
    feature_vector: np.ndarray | None = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "component": self.detection.component,
            "bbox": list(self.detection.bbox),
            "detection_score": self.detection.score,
            "detection_source": self.detection.source,
            "mask_area_ratio": self.mask_area_ratio,
            "mask_edge_contact_ratio": self.mask_edge_contact_ratio,
            "segmentation_valid": self.segmentation_valid,
            "predictions": [asdict(value) for value in self.predictions],
            "feature_lengths": self.feature_lengths,
            "warnings": self.warnings,
        }


@dataclass
class OutfitDecision:
    outfit_id: str
    decision: ComplianceDecision
    rules: list[RuleResult]
    components: list[ComponentAnalysis]
    reason: str
    warnings: list[str] = field(default_factory=list)

    @property
    def passed_reasons(self) -> list[str]:
        return [rule.reason or rule.rule_id for rule in self.rules if rule.status.value == "pass"]

    @property
    def failed_reasons(self) -> list[str]:
        return [rule.reason or rule.rule_id for rule in self.rules if rule.status.value == "fail"]

    @property
    def review_reasons(self) -> list[str]:
        return [
            rule.reason or rule.rule_id
            for rule in self.rules
            if rule.status.value in {"unknown", "not_applicable"}
        ]

    @property
    def unsupported_reasons(self) -> list[str]:
        return [
            rule.reason or rule.rule_id
            for rule in self.rules
            if rule.status.value == "unsupported"
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "outfit_id": self.outfit_id,
            "decision": self.decision.value,
            "reason": self.reason,
            "passed_reasons": self.passed_reasons,
            "failed_reasons": self.failed_reasons,
            "review_reasons": self.review_reasons,
            "unsupported_reasons": self.unsupported_reasons,
            "rules": [
                {
                    **asdict(rule),
                    "status": rule.status.value,
                }
                for rule in self.rules
            ],
            "components": [component.to_dict() for component in self.components],
            "warnings": self.warnings,
        }


@dataclass
class ImageDecisionReport:
    decision: ComplianceDecision
    outfits: list[OutfitDecision]
    reason: str
    timings_ms: dict[str, float]
    warnings: list[str]
    image_shape: tuple[int, int, int]
    scale: float
    pipeline_version: str = "classical-attire-v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_version": self.pipeline_version,
            "decision": self.decision.value,
            "user_facing_decision": {
                "compliant": "appropriate",
                "non_compliant": "inappropriate",
                "review_required": "review required",
            }[self.decision.value],
            "reason": self.reason,
            "outfits": [outfit.to_dict() for outfit in self.outfits],
            "timings_ms": self.timings_ms,
            "warnings": self.warnings,
            "image_shape": list(self.image_shape),
            "scale": self.scale,
        }


def aggregate_outfit_decisions(
    outfits: list[OutfitDecision],
) -> tuple[ComplianceDecision, str]:
    if not outfits:
        return ComplianceDecision.REVIEW_REQUIRED, "No attire components were detected."
    failed = [outfit.outfit_id for outfit in outfits if outfit.decision is ComplianceDecision.NON_COMPLIANT]
    if failed:
        return (
            ComplianceDecision.NON_COMPLIANT,
            f"At least one outfit is inappropriate: {', '.join(failed)}.",
        )
    uncertain = [outfit.outfit_id for outfit in outfits if outfit.decision is ComplianceDecision.REVIEW_REQUIRED]
    if uncertain:
        return (
            ComplianceDecision.REVIEW_REQUIRED,
            f"No confident failure was found, but review is required for: {', '.join(uncertain)}.",
        )
    return ComplianceDecision.COMPLIANT, "Every detected outfit passes the supported rubric."
