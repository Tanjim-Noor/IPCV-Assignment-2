#!/usr/bin/env python3
"""Validate an Ultimate Research Passport and its cross-field invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker


def validate(passport_path: Path, schema_path: Path | None = None) -> list[str]:
    schema_path = schema_path or Path(__file__).resolve().parents[1] / "shared" / "research-passport.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    passport = yaml.safe_load(passport_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(passport), key=lambda item: list(item.absolute_path))
    ]
    if not isinstance(passport, dict):
        return errors

    experiments = passport.get("experiments", {})
    if not experiments.get("execution_approved", False):
        active = [
            item.get("id", "<unknown>")
            for item in experiments.get("records", [])
            if item.get("status") in {"running", "completed"}
        ]
        if active:
            errors.append(
                "experiments/execution_approved: approval is required for running or completed records: "
                + ", ".join(active)
            )
    missing_provenance = [
        item.get("id", "<unknown>")
        for item in experiments.get("records", [])
        if item.get("status") == "completed" and not item.get("provenance")
    ]
    if missing_provenance:
        errors.append(
            "experiments/records: completed experiments require non-empty provenance: "
            + ", ".join(missing_provenance)
        )

    certification = passport.get("certification", {}).get("status")
    if certification in {"verified", "submission-ready"}:
        unsupported_claims = [
            item.get("claim_id", "<unknown>")
            for item in passport.get("evidence", {}).get("claim_mappings", [])
            if item.get("verification_state") != "verified" or not item.get("source_ids")
        ]
        if unsupported_claims:
            errors.append(
                "evidence/claim_mappings: verified certification requires supported, verified claims: "
                + ", ".join(unsupported_claims)
            )
        stale_artifacts = [
            item.get("path", "<unknown>")
            for item in passport.get("artifacts", [])
            if item.get("verification_state") != "verified"
        ]
        if stale_artifacts:
            errors.append(
                "artifacts: verified certification requires every recorded artifact to be verified: "
                + ", ".join(stale_artifacts)
            )
        unresolved = [
            item.get("id", "<unknown>")
            for item in passport.get("review", {}).get("issues", [])
            if item.get("resolution_state") == "open"
        ]
        if unresolved:
            errors.append(
                "review/issues: verified certification cannot retain open issues: "
                + ", ".join(unresolved)
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("passport", type=Path)
    parser.add_argument("--schema", type=Path)
    args = parser.parse_args()
    errors = validate(args.passport, args.schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Valid Research Passport: {args.passport}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
