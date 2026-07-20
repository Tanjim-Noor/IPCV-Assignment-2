# Review, Revision, and Reviewer Response

## Contents

- Independent review
- Issue priority
- Revision ledger
- Targeted revision
- Response letters
- Rebuttal audit
- Stopping

## Independent review

Review the artifact as if encountering it fresh:

1. Contribution and venue fit.
2. Question/design alignment.
3. Argument and evidence.
4. Methods and reproducibility.
5. Results and interpretation.
6. Citations and integrity.
7. Organization, style, tables, figures, and compliance.

Support every finding with a location and explanation. Separate defects from preferences.

## Issue priority

- `P0 critical`: invalidates central claims, integrity, ethics, or required compliance.
- `P1 major`: materially weakens contribution, design, reasoning, or interpretability.
- `P2 moderate`: localized ambiguity, missing support, or organization problem.
- `P3 minor`: style, consistency, or presentation.

Resolve dependencies first; a changed research question may invalidate several later edits.

## Revision ledger

Use one row per concern:

| ID | Source/comment | Priority | Interpretation | Decision | Planned change | Location | Evidence | Status |
|---|---|---|---|---|---|---|---|---|

Allowed decisions: accept, partially accept, clarify, respectfully disagree, or cannot resolve. Never omit a concern silently.

## Targeted revision

1. Identify the canonical draft.
2. Anchor blocks before editing.
3. Limit changes to blocks required by the ledger.
4. Verify that neighboring logic and cross-references remain valid.
5. Produce an apply report listing changed and untouched blocks.
6. Re-run citation and integrity checks on affected claims.

Use `scripts/anchorize_draft.py` and `scripts/apply_revision_patch.py` when deterministic patching is appropriate.

## Response letters

For each comment:

1. Thank or acknowledge without empty repetition.
2. State the interpretation of the concern.
3. State the action and rationale.
4. Quote or summarize the revised text briefly.
5. Give exact manuscript location.
6. If disagreeing, remain specific, respectful, and evidence-based.

Do not claim a change that is absent from the manuscript.

## Rebuttal audit

When both reviewer comments and an existing response are supplied, audit rather than generate:

- Map every comment to a response.
- Mark addressed, partial, missing, or unverifiable.
- Check tone, evidence, and location claims.
- Identify contradictions between the response and revised manuscript.

An audited response is not submission-ready unless manuscript changes are also verified.

## Stopping

Use at most two substantive revision rounds by default. Stop earlier when:

- No P0 issue remains.
- P1 issues are resolved or explicitly accepted as limitations.
- A new round produces no material improvement.
- Additional rewriting risks meaning or version drift.

Never conceal unresolved issues to satisfy a loop limit.

