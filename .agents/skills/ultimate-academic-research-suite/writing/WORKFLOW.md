---
name: academic-writing
description: Comprehensive, portable academic writing workflow for evidence-grounded planning, drafting, revising, and preparing scholarly outputs. Use for journal or conference papers, thesis chapters, literature reviews, theoretical papers, grants, abstracts, citation and integrity audits, reviewer responses, rebuttal audits, academic style, phrase selection, formatting, and submission preparation in the user's requested language.
license: See LICENSE.md and THIRD_PARTY_NOTICES.md
compatibility: Portable Agent Skills package. Python 3.9+ is optional and used only for standard-library helper scripts.
metadata:
  author: Tanjim-Noor
  version: "1.0.0"
  repository: https://github.com/Tanjim-Noor/academic-writing-skill
---

# Academic Writing

Produce defensible scholarly work through explicit evidence, argument, integrity, revision, and formatting gates. Follow the user's requested language and venue requirements. Use the English Academic Phrasebank only when the target prose is English.

## Non-negotiable rules

1. Never invent sources, bibliographic metadata, quotations, data, methods, results, policies, or review outcomes.
2. Distinguish verified evidence, author-provided claims, inference, proposal, and placeholder text.
3. Do not certify an artifact as verified or submission-ready while critical integrity issues remain.
4. Verify time-sensitive venue, funder, open-access, disclosure, and submission rules against current primary sources.
5. Preserve the author's meaning and evidence strength during editing.
6. Establish content before selecting phrasebank language; never let a stock phrase create a claim.
7. Ask only for information that materially changes the work and cannot be derived from supplied materials.

## Select a mode

| Mode | Use when | Primary output |
|---|---|---|
| `full` | Build an output through all relevant phases | Complete scholarly package |
| `plan` | Clarify question, contribution, evidence, and work sequence | Writing brief and phase plan |
| `outline` | Design structure before drafting | Evidence-mapped outline |
| `draft` | Draft one or more sections from adequate evidence | Section draft with evidence markers |
| `literature-review` | Search, organize, and synthesize prior work | Review protocol, matrix, and synthesis |
| `abstract` | Draft or revise an abstract | Structured or unstructured abstract and keywords |
| `grant` | Develop a research or funding proposal | Aims, narrative, impact, and budget rationale |
| `revise` | Improve a draft against objectives or feedback | Revision ledger and targeted revision |
| `reviewer-response` | Plan responses or audit an existing rebuttal | Comment ledger and response letter |
| `citation-audit` | Check claims, citations, and references | Traceable integrity report |
| `format` | Convert or normalize document presentation | Venue-aligned output package |
| `submission` | Prepare final administrative materials | Submission checklist and supporting documents |

Read [modes-and-intake.md](references/modes-and-intake.md) for mode gates and the complete Writing Brief.

## Run the core workflow

### 1. Intake and classify

- Identify deliverable, audience, discipline, language, venue, length, citation style, output format, deadline, supplied materials, and evidence status.
- Determine whether the user wants guidance, generation, revision, audit, or formatting.
- Record assumptions and unresolved decisions.

### 2. Establish research and evidence readiness

- Refine the question, contribution, scope, and design.
- Inventory supplied sources and separate verified from unverified material.
- Build a search or evidence-completion plan when support is insufficient.
- Read [research-design-and-evidence.md](references/research-design-and-evidence.md).

### 3. Design structure and argument

- Select the deliverable pattern and venue constraints.
- Allocate sections and word count.
- Map each substantive claim to evidence, reasoning, counterpoints, and limitations.
- Read [structures-and-deliverables.md](references/structures-and-deliverables.md) and [argumentation-and-drafting.md](references/argumentation-and-drafting.md).

### 4. Draft section by section

- Draft from the approved outline and evidence map.
- Mark unsupported points explicitly instead of filling gaps.
- Maintain terminology, tense, voice, and contribution boundaries.
- Keep results separate from interpretation unless the genre combines them.

### 5. Audit citations, integrity, style, and language

- Reconcile every in-text citation with the reference list.
- Trace important claims to adequate sources.
- Check data, methods, results, quotations, authorship, disclosure, and originality.
- Calibrate certainty and improve cohesion without changing claim strength.
- Read [citation-integrity-and-ethics.md](references/citation-integrity-and-ethics.md) and [style-and-language.md](references/style-and-language.md).

### 6. Review and revise

- Review contribution, logic, evidence, methods, presentation, and compliance independently.
- Prioritize critical issues before stylistic preferences.
- Use a comment-to-change ledger and targeted patches.
- Stop after at most two substantive loops by default or earlier when no critical issue remains and improvement has converged.
- Read [review-revision-and-response.md](references/review-revision-and-response.md).

### 7. Format and finalize

- Apply the current venue template and citation style.
- Validate tables, figures, equations, cross-references, accessibility, and rendered output.
- Prepare cover letter, declarations, funding/authorship statements, data/code availability, and AI-use disclosure when required.
- Read [publication-and-formatting.md](references/publication-and-formatting.md).

Read [workflow-core.md](references/workflow-core.md) for checkpoints, state, recovery, and completion statuses.

## Use the phrasebank

1. Identify the rhetorical function required.
2. Search the index rather than loading the full bank:

```bash
python scripts/search_phrasebank.py --section discussing-findings --query limitation --limit 12
python scripts/search_phrasebank.py --function "being cautious" --entry-type phrase --limit 20
```

3. Inspect source page and subheading.
4. Adapt placeholders, grammar, discipline terms, and certainty.
5. Audit repetition and confirm the phrase does not introduce unsupported content.

Read [phrasebank-routing.md](references/phrasebank-routing.md) first. Then load only the relevant direct reference:

- Paper sections: [introducing work](references/phrasebank-introducing-work.md), [literature](references/phrasebank-referring-to-literature.md), [methods](references/phrasebank-describing-methods.md), [results](references/phrasebank-reporting-results.md), [discussion](references/phrasebank-discussing-findings.md), [conclusions](references/phrasebank-writing-conclusions.md).
- Reasoning functions: [criticality](references/phrasebank-being-critical.md), [caution](references/phrasebank-being-cautious.md), [classification](references/phrasebank-classifying-and-listing.md), [comparison](references/phrasebank-compare-and-contrast.md), [definitions](references/phrasebank-defining-terms.md), [trends](references/phrasebank-describing-trends.md), [quantities](references/phrasebank-describing-quantities.md), [causality](references/phrasebank-explaining-causality.md), [examples](references/phrasebank-giving-examples.md), [transitions](references/phrasebank-signalling-transition.md), and [past time](references/phrasebank-writing-about-the-past.md).
- Language notes: [about and use](references/phrasebank-about-and-use.md), [academic style](references/phrasebank-academic-style.md), [confused words](references/phrasebank-commonly-confused-words.md), [British/US spelling](references/phrasebank-british-and-us-spelling.md), [punctuation](references/phrasebank-punctuation.md), [articles](references/phrasebank-using-articles.md), [sentence structure](references/phrasebank-sentence-structure.md), and [paragraphs/tips](references/phrasebank-paragraph-structure-and-tips.md).

## Use deliverable-specific guidance

- Grants: read [grants-and-proposals.md](references/grants-and-proposals.md).
- Abstracts, theses, reviews, theoretical papers, conferences, and policy briefs: read [structures-and-deliverables.md](references/structures-and-deliverables.md).
- Multilingual work: draft in the target language; use English phrasebank material only for English passages. Preserve technical terms when translation would reduce precision.
- Templates: copy the appropriate file from `assets/templates/` and adapt it to the current venue.

## Completion contract

Return only statuses supported by evidence:

- `planned`: brief, scope, and workflow agreed.
- `drafted`: requested text exists but has not passed all audits.
- `audited-with-issues`: audit complete; unresolved issues listed.
- `verified`: required checks passed against available evidence.
- `submission-ready`: verified, venue-formatted, rendered, and administratively complete.

Always list unresolved evidence gaps, placeholders, unverified policies, and user decisions separately from the finished prose.
