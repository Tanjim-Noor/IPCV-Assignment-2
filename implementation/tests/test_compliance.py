import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from ipcv_attire.compliance import (  # noqa: E402
    ComplianceDecision,
    RuleResult,
    RuleStatus,
    decide_compliance,
)


class ComplianceDecisionTests(unittest.TestCase):
    def test_all_required_rules_pass(self) -> None:
        result = decide_compliance(
            [
                RuleResult("collared_top", RuleStatus.PASS, 0.9),
                RuleResult("formal_bottom", RuleStatus.PASS, 0.8),
                RuleResult("footwear_present", RuleStatus.PASS, 0.95),
            ]
        )
        self.assertEqual(result.decision, ComplianceDecision.COMPLIANT)

    def test_confident_failure_is_non_compliant(self) -> None:
        result = decide_compliance(
            [
                RuleResult("round_neck_tshirt", RuleStatus.FAIL, 0.9),
                RuleResult("formal_bottom", RuleStatus.PASS, 0.8),
            ]
        )
        self.assertEqual(result.decision, ComplianceDecision.NON_COMPLIANT)

    def test_unknown_required_rule_needs_review(self) -> None:
        result = decide_compliance(
            [
                RuleResult("footwear_subtype", RuleStatus.UNKNOWN, reason="Feet are occluded"),
                RuleResult("formal_bottom", RuleStatus.PASS, 0.8),
            ]
        )
        self.assertEqual(result.decision, ComplianceDecision.REVIEW_REQUIRED)

    def test_low_confidence_failure_needs_review(self) -> None:
        result = decide_compliance(
            [RuleResult("damaged_bottom", RuleStatus.FAIL, 0.4)]
        )
        self.assertEqual(result.decision, ComplianceDecision.REVIEW_REQUIRED)

    def test_duplicate_rule_ids_need_review(self) -> None:
        result = decide_compliance(
            [
                RuleResult("headwear", RuleStatus.PASS, 0.8),
                RuleResult("headwear", RuleStatus.FAIL, 0.8),
            ]
        )
        self.assertEqual(result.decision, ComplianceDecision.REVIEW_REQUIRED)


if __name__ == "__main__":
    unittest.main()
