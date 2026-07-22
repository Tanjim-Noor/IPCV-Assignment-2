"""Convert target probabilities into complete, auditable rule outcomes."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .compliance import ComplianceResult, RuleResult, RuleStatus, decide_compliance
from .reporting import TargetPrediction


UNSUPPORTED_LABELS = {
    "tucked_in_shirt": "Tucked-in shirt status is not annotated by Fashionpedia.",
    "excessive_body_piercings": "Excessive body piercings are not annotated by Fashionpedia.",
    "open_toe_footwear_subtype": "Exact open-toe footwear subtype is not annotated by Fashionpedia.",
    "customary_headgear_exception": "Customary-headgear exceptions are not annotated by Fashionpedia.",
}


def _prediction_status(
    prediction: TargetPrediction,
    *,
    kind: str,
    region_visible: bool,
) -> RuleStatus:
    if prediction.probability >= prediction.high_threshold:
        return RuleStatus.PASS if kind == "required" else RuleStatus.FAIL
    if prediction.probability <= prediction.low_threshold:
        if kind == "prohibited":
            return RuleStatus.PASS
        return RuleStatus.FAIL if region_visible else RuleStatus.UNKNOWN
    return RuleStatus.UNKNOWN


def evaluate_rubric(
    predictions: Iterable[TargetPrediction],
    policy: Mapping[str, Any],
    *,
    visible_regions: set[str],
    extra_review_reasons: Iterable[str] = (),
) -> ComplianceResult:
    """Evaluate every supported and unsupported rule without early-returning."""

    by_target = {prediction.target_id: prediction for prediction in predictions}
    definitions = policy["compliance_rules"]["rule_definitions"]
    rules: list[RuleResult] = []
    for target in policy["derived_targets"]:
        definition = definitions[target]
        label = definition["label"]
        region = definition["region"]
        kind = definition["kind"]
        severity = definition["severity"]
        if not definition["model_supported"]:
            rules.append(
                RuleResult(
                    target,
                    RuleStatus.UNSUPPORTED,
                    evidence_region=region,
                    reason=f"{label} is unsupported by the available class support and was not guessed.",
                    required=False,
                    severity=severity,
                    supported=False,
                )
            )
            continue
        prediction = by_target.get(target)
        if prediction is None:
            rules.append(
                RuleResult(
                    target,
                    RuleStatus.UNKNOWN,
                    evidence_region=region,
                    reason=f"{label}: no reliable model evidence was produced.",
                    severity=severity,
                )
            )
            continue
        status = _prediction_status(
            prediction, kind=kind, region_visible=region in visible_regions
        )
        if status is RuleStatus.PASS:
            reason = f"{label} passed with confidence {prediction.probability:.3f}."
        elif status is RuleStatus.FAIL:
            reason = f"{label} failed with confidence {prediction.probability:.3f}."
        else:
            reason = (
                f"{label} is uncertain at {prediction.probability:.3f}; "
                "the result remains review-required."
            )
        rules.append(
            RuleResult(
                target,
                status,
                confidence=prediction.probability,
                evidence_region=prediction.evidence_region or region,
                reason=reason,
                severity=severity,
            )
        )

    for unsupported in policy["compliance_rules"]["unsupported_conditions"]:
        rules.append(
            RuleResult(
                unsupported,
                RuleStatus.UNSUPPORTED,
                reason=UNSUPPORTED_LABELS.get(unsupported, f"{unsupported} is unsupported."),
                required=False,
                supported=False,
            )
        )
    for index, reason in enumerate(extra_review_reasons, start=1):
        rules.append(
            RuleResult(
                f"technical_review_{index}",
                RuleStatus.UNKNOWN,
                reason=reason,
                severity="technical",
            )
        )
    return decide_compliance(rules, minimum_confidence=0.0)

