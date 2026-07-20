#!/usr/bin/env python3
"""Conservatively migrate an upstream Material Passport to Research Passport 1.0."""

from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import yaml

from validate_research_passport import validate


def first(source: dict, *names: str, default=None):
    for name in names:
        if name in source and source[name] is not None:
            return source[name]
    return default


def migrate(source_path: Path) -> dict:
    source = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    return {
        "schema_version": "1.0",
        "project": {
            "deliverable": str(first(source, "deliverable", "paper_type", default="academic deliverable")),
            "language": str(first(source, "language", default="user-requested language")),
            "audience": str(first(source, "audience", default="scholarly audience")),
            "venue": first(source, "venue", "journal"),
            "citation_style": first(source, "citation_style"),
            "output_format": str(first(source, "output_format", default="Markdown")),
        },
        "workflow": {
            "route": "unified-pipeline",
            "mode": str(first(source, "mode", default="pipeline")),
            "current_stage": first(source, "current_stage", "stage", default=1),
            "writing_phase": first(source, "writing_phase"),
            "checkpoint": "migrated-state-review",
            "revision_round": min(int(first(source, "revision_round", default=0)), 2),
        },
        "research": {
            "approved_question": first(source, "approved_question", "research_question"),
            "scope": first(source, "scope", default={}),
            "design": first(source, "design", "methodology", default={}),
            "search_protocol": first(source, "search_protocol", default={}),
            "corpus_version": first(source, "corpus_version"),
        },
        "evidence": {
            "sources": [],
            "claim_mappings": [],
        },
        "experiments": {
            "intake_declared": True,
            "execution_approved": False,
            "records": [],
        },
        "decisions": [
            {
                "decision": f"Migrated Material Passport from {source_path} with SHA-256 {source_hash}",
                "actor": "agent",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "artifacts": [],
        "review": {"issues": []},
        "integrity": {
            "status": "INSUFFICIENT-EVIDENCE",
            "stale": True,
            "checks": [],
            "critical_findings": [],
        },
        "certification": {
            "status": "planned",
            "venue_formatting_complete": False,
            "rendered_output_inspected": False,
            "administrative_complete": False,
        },
        "next_action": {
            "gate": "review-migrated-state",
            "responsible_party": "user",
            "required_inputs": ["Confirm migrated project, research, and workflow fields"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("material_passport", type=Path)
    parser.add_argument("research_passport", type=Path)
    args = parser.parse_args()
    passport = migrate(args.material_passport)
    args.research_passport.parent.mkdir(parents=True, exist_ok=True)
    args.research_passport.write_text(
        yaml.safe_dump(passport, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
        newline="\n",
    )
    errors = validate(args.research_passport)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Migrated Research Passport: {args.research_passport}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
