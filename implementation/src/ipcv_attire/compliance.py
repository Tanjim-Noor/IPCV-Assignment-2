"""Auditable three-way dress-code decision logic.

The module intentionally contains no learned or deep-learning component. Model
predictions are converted to rule results elsewhere; this module only combines
those explicit results into a final decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class RuleStatus(str, Enum):
    """Status of one policy rule for a single person or outfit."""

    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class ComplianceDecision(str, Enum):
    """Final system output required by the dataset policy."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REVIEW_REQUIRED = "review_required"


@dataclass(frozen=True)
class RuleResult:
    """Evidence and outcome for one transparent dress-code rule."""

    rule_id: str
    status: RuleStatus
    confidence: float | None = None
    evidence_region: str | None = None
    reason: str | None = None
    required: bool = True

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class ComplianceResult:
    """Final decision plus the complete rule-level audit trail."""

    decision: ComplianceDecision
    rules: tuple[RuleResult, ...]
    reason: str


def decide_compliance(
    rule_results: Iterable[RuleResult],
    *,
    minimum_confidence: float = 0.5,
) -> ComplianceResult:
    """Combine rule results without forcing unsupported binary decisions.

    A confident rule failure is non-compliant. Missing, unsupported, low-
    confidence, or conflicting required evidence is sent to manual review.
    Only a complete set of passing required rules can be compliant.
    """

    rules = tuple(rule_results)
    if not rules:
        return ComplianceResult(
            ComplianceDecision.REVIEW_REQUIRED,
            rules,
            "No rule evidence was supplied.",
        )

    seen: set[str] = set()
    duplicates: set[str] = set()
    for rule in rules:
        if rule.rule_id in seen:
            duplicates.add(rule.rule_id)
        seen.add(rule.rule_id)
    if duplicates:
        names = ", ".join(sorted(duplicates))
        return ComplianceResult(
            ComplianceDecision.REVIEW_REQUIRED,
            rules,
            f"Conflicting duplicate rule results: {names}.",
        )

    confident_failures = [
        rule
        for rule in rules
        if rule.status is RuleStatus.FAIL
        and (rule.confidence is None or rule.confidence >= minimum_confidence)
    ]
    if confident_failures:
        names = ", ".join(rule.rule_id for rule in confident_failures)
        return ComplianceResult(
            ComplianceDecision.NON_COMPLIANT,
            rules,
            f"One or more dress-code rules failed: {names}.",
        )

    review_rules = [
        rule
        for rule in rules
        if rule.required
        and (
            rule.status in {RuleStatus.UNKNOWN, RuleStatus.NOT_APPLICABLE}
            or (rule.confidence is not None and rule.confidence < minimum_confidence)
        )
    ]
    if review_rules:
        names = ", ".join(rule.rule_id for rule in review_rules)
        return ComplianceResult(
            ComplianceDecision.REVIEW_REQUIRED,
            rules,
            f"Required evidence is missing, unsupported, or uncertain: {names}.",
        )

    unresolved_failures = [rule for rule in rules if rule.status is RuleStatus.FAIL]
    if unresolved_failures:
        names = ", ".join(rule.rule_id for rule in unresolved_failures)
        return ComplianceResult(
            ComplianceDecision.REVIEW_REQUIRED,
            rules,
            f"A possible rule failure is below the confidence threshold: {names}.",
        )

    required = [rule for rule in rules if rule.required]
    if not required or any(rule.status is not RuleStatus.PASS for rule in required):
        return ComplianceResult(
            ComplianceDecision.REVIEW_REQUIRED,
            rules,
            "The required rule set is incomplete.",
        )

    return ComplianceResult(
        ComplianceDecision.COMPLIANT,
        rules,
        "All required, supported dress-code rules passed.",
    )
