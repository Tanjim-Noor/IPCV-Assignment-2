"""Classical end-to-end utilities for the IPCV attire project."""

from .compliance import (
    ComplianceDecision,
    ComplianceResult,
    RuleResult,
    RuleStatus,
    decide_compliance,
)
from .dataset_policy import (
    build_manifest_bundle,
    derive_compliance_label,
    derive_targets,
    load_policy,
    require_showcase_approval,
    validate_annotation_data,
)
from .pipeline import AttirePipeline, RecognitionArtifact
from .reporting import ImageDecisionReport, OutfitDecision, TargetPrediction

__all__ = [
    "ComplianceDecision",
    "ComplianceResult",
    "RuleResult",
    "RuleStatus",
    "AttirePipeline",
    "ImageDecisionReport",
    "OutfitDecision",
    "RecognitionArtifact",
    "TargetPrediction",
    "build_manifest_bundle",
    "derive_compliance_label",
    "decide_compliance",
    "derive_targets",
    "load_policy",
    "require_showcase_approval",
    "validate_annotation_data",
]
