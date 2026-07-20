# Research Passport

Use `academic-research/research-passport.yaml` as the only cross-workflow state carrier unless the user chooses another path. Validate it before reading state and after every update.

## Required sections

`schema_version`, `project`, `workflow`, `research`, `evidence`, `experiments`, `decisions`, `artifacts`, `review`, `integrity`, `certification`, and `next_action` are required. The authoritative structure and enums are in `research-passport.schema.json`.

## Update protocol

1. Load and validate the current passport.
2. Recompute SHA-256 hashes for artifacts used by the active stage.
3. If an artifact hash changed, mark its verification and every dependent integrity or certification result stale.
4. Apply only the current workflow's state transition.
5. Append user approvals, rejected options, overrides, and risk decisions to `decisions`.
6. Record the next gate, responsible party, and required inputs in `next_action`.
7. Validate the complete result before saving it atomically.

## Workflow authority

- Deep research owns the approved question, scope, search protocol, corpus, and evidence verification.
- Writing owns the Writing Brief, outline, claim map, drafts, revision ledger, formatting, and submission materials.
- Experiment workflow owns protocols and experiment provenance. Planning does not authorize execution.
- Review workflow owns reviewer findings, editorial synthesis, and re-review results; it never edits manuscript artifacts.
- Integrity workflow owns integrity checks and status but cannot overwrite evidence or reviewer history.
- The root router owns stage transitions and certification.

## Staleness

Content hashes, not timestamps, determine staleness. When a parent artifact changes, mark dependent claim mappings, review resolutions, integrity checks, and certification stale. Reverification must use the current artifact content.

## Integrity and certification

Integrity values are `PASS`, `PASS-WITH-WARNINGS`, `FAIL`, and `INSUFFICIENT-EVIDENCE`. Certification values are `planned`, `drafted`, `audited-with-issues`, `verified`, and `submission-ready`.

`verified` requires current hashes, no critical finding, and passing required checks. `submission-ready` additionally requires venue formatting, rendered-output inspection, and administrative completion. Risk acceptance is recorded as a decision but does not change failed evidence into passing evidence.

## Migration

Run `scripts/migrate_material_passport.py` once for an upstream Material Passport. Preserve its source path and hash, map available fields conservatively, default experiment execution approval to false unless an explicit user approval exists, mark unverifiable prior integrity stale, and validate the resulting Research Passport before use.
