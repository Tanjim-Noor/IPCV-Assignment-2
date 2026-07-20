# Unified Academic Pipeline

Coordinate research, writing, integrity, review, revision, finalization, and certification through one Research Passport. This workflow orchestrates; it does not replace the specialist workflows.

## State

Use `academic-research/research-passport.yaml` unless the user selected another path. Validate before reading and after every update. Resume from the earliest incomplete stage whose input artifact hashes remain current.

## Ten stages

1. **Research** — Run [deep research](../deep-research/WORKFLOW.md). Stop for research-question approval and corpus approval.
2. **Write** — Run [writing](../../writing/WORKFLOW.md). Produce the Writing Brief, evidence map, approved outline, claim map, drafts, and figures.
3. **Pre-review integrity** — Audit references, claim support, data, methods, results, originality, disclosure, and research failure modes. Block on `FAIL` or `INSUFFICIENT-EVIDENCE`.
4. **Independent review** — Run the [reviewer workflow](../academic-paper-reviewer/WORKFLOW.md) without modifying the manuscript.
5. **Revision** — Run writing `revise` through a comment-to-change ledger and produce a response-to-reviewers artifact.
6. **Re-review** — Run reviewer `re-review`; verify revision claims and record residual issues.
7. **Final revision** — Permit one final substantive revision round. The total substantive revision count cannot exceed two.
8. **Final integrity** — Re-run integrity from scratch against current hashes. Do not reuse stale findings.
9. **Finalize** — Run writing `format` and `submission`; validate citations, tables, figures, equations, accessibility, rendered output, declarations, and administrative materials.
10. **Certification** — Record collaboration, decisions, unresolved warnings, limitations, and the final completion status.

## Transition rules

- Route experiment work through [experiment workflow](../experiment-agent/WORKFLOW.md) and stop for explicit execution approval.
- Any artifact hash change marks dependent evidence, review, integrity, and certification stale.
- Reviewers remain read-only.
- `verified` requires current passing integrity and no unresolved critical finding.
- `submission-ready` additionally requires venue formatting, rendered-output inspection, and administrative completion.
- User risk acceptance is recorded but never changes failed evidence into verified evidence.
- Missing required tools or evidence produce `INSUFFICIENT-EVIDENCE`.
- On context drift, reload the passport, verify hashes, and resume from the latest valid checkpoint.

Use ARS role prompts inline by default. Subagent delegation and external model or API uploads require explicit user authorization.
