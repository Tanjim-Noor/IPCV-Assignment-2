# Academic Paper Compatibility Workflow

This entrypoint preserves ARS academic-paper modes while delegating all writing behavior to the canonical [writing workflow](../../writing/WORKFLOW.md). It is not an independent writing engine.

## State

Validate `academic-research/research-passport.yaml` before routing. Record the writing mode, phase, checkpoint, artifact versions, decisions, and next action after each transition.

## Mode mapping

| ARS mode | Writing mode |
|---|---|
| `full` | `full` |
| `plan` | `plan` |
| `outline-only` | `outline` |
| `revision` | `revise` |
| `revision-coach` | `reviewer-response` planning |
| `abstract-only` | `abstract` |
| `lit-review` | `literature-review` |
| `format-convert` | `format` |
| `citation-check` | `citation-audit` |
| `disclosure` | `submission` plus disclosure protocol |
| `rebuttal-audit` | `reviewer-response` audit |

The writing engine additionally retains `draft`, `grant`, and `submission`.

If `lit-review` requests source discovery rather than writing from an approved corpus, return to [deep research](../deep-research/WORKFLOW.md).

## Non-negotiable boundaries

- Establish claims and evidence before drafting.
- Use English phrasebank material only for English target prose.
- Do not fabricate citations, findings, methods, policies, or missing text.
- Keep revision changes anchored and preserve untouched content.
- Limit substantive revision to two rounds in the unified pipeline.
- Update and validate the Research Passport before returning control.
