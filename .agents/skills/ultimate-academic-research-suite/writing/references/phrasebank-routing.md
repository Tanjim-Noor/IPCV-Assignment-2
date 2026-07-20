# Academic Phrasebank Routing

## Purpose

Use the phrasebank as a rhetorical language resource, not as a source of evidence or ideas. The local index contains 3,744 page-traceable nonblank lines from all 107 physical PDF pages and all 25 content areas.

## Retrieval workflow

1. Name the rhetorical purpose: introduce importance, describe a method, qualify a claim, compare studies, report a trend, state a limitation, or transition.
2. Search the JSONL index with `scripts/search_phrasebank.py`.
3. Load the corresponding section reference only.
4. Select a small number of candidates.
5. Adapt placeholders, number, tense, voice, discipline terminology, and certainty.
6. Confirm the sentence remains accurate when read without the stock phrase.
7. Audit nearby prose for repetition.

## Search fields

- `section`: stable section slug.
- `function`: matches section title or subheading.
- `query`: case-insensitive text search.
- `entry_type`: heading, phrase, bullet, table-row, or note.
- `limit`: maximum returned records.

Each result includes physical PDF page, printed page, subheading, and source checksum.

## Section routing

| Need | Section |
|---|---|
| Establish context, gap, aim, questions, value, or structure | `introducing-work` |
| Summarize, attribute, compare, or criticize sources | `referring-to-literature` |
| Describe design, sample, materials, procedure, or analysis | `describing-methods` |
| Report quantities, patterns, tests, tables, and figures | `reporting-results` |
| Interpret, compare, explain, qualify, and limit findings | `discussing-findings` |
| Summarize contribution, implications, limitations, and future work | `writing-conclusions` |
| Evaluate strengths, weaknesses, gaps, and alternatives | `being-critical` |
| Hedge certainty and generalization | `being-cautious` |
| Define, classify, compare, quantify, explain, exemplify, or transition | Corresponding general-function file |
| Check style, spelling, punctuation, articles, sentences, or paragraphs | Corresponding language-note file |

## Safety rules

- Do not insert a phrase containing a claim the evidence does not support.
- Replace illustrative content words and placeholders.
- Do not reproduce long distinctive passages as if they were original prose.
- Cite ideas and evidence even when their wording uses a generic phrase.
- Do not use English phrases in non-English output unless quoting or explicitly discussing English.
- Prefer one adapted phrase over several formulaic phrases in the same paragraph.

