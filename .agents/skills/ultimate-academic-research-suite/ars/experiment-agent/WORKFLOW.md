# Experiment Workflow

Use this workflow for study protocols, code experiments, statistical interpretation, and reproducibility.

## Mode compatibility

| Canonical mode | Upstream alias |
|---|---|
| `study-protocol` | `plan`, `manage` |
| `code-experiment` | `run` |
| `statistical-interpretation` | `validate` |
| `reproducibility` | `validate` |

## State and approval

Load and validate the Research Passport. Record an explicit experiment intake declaration even when no experiment is needed.

Planning, protocol design, code inspection, and interpretation do not authorize execution. Before running code, collecting data, training a model, contacting participants, or changing an external system:

1. Present the exact operation, inputs, environment, expected duration, outputs, risks, and cost.
2. Obtain explicit user approval.
3. Append the approval decision and timestamp to the Research Passport.
4. Set `experiments.execution_approved: true` only for the approved scope.

## Provenance

Record the protocol version, code and configuration hashes, data identifiers and access conditions, environment, random seeds, software versions, hardware, timestamps, outputs, failures, deviations, and statistical assumptions. Experiment claims without this provenance cannot pass integrity.

Do not interpret statistical significance as practical importance. Report uncertainty, assumptions, missingness, multiplicity, effect sizes, and limitations. Human studies remain subject to applicable ethics and institutional approval; this workflow cannot grant ethical approval.

Use role prompts under `agents/` inline by default. Delegate only after explicit user authorization. External compute or API uploads require explicit consent.
