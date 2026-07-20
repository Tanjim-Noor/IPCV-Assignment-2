#!/usr/bin/env python3
"""Search the bundled page-traceable Academic Phrasebank index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def contains(value: str | None, query: str | None) -> bool:
    return query is None or query.casefold() in (value or "").casefold()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--section", help="Exact stable section slug")
    parser.add_argument("--function", dest="function_name", help="Text in section title or subheading")
    parser.add_argument("--query", help="Case-insensitive text search")
    parser.add_argument(
        "--entry-type", choices=["heading", "phrase", "bullet", "table-row", "note"]
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--format", choices=["markdown", "jsonl"], default="markdown")
    parser.add_argument("--index", type=Path)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")

    index = args.index or Path(__file__).resolve().parents[1] / "references" / "phrasebank-index.jsonl"
    matches: list[dict] = []
    with index.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if args.section and record["section"] != args.section:
                continue
            if args.entry_type and record["entry_type"] != args.entry_type:
                continue
            if args.function_name and not (
                contains(record.get("section_title"), args.function_name)
                or contains(record.get("subheading"), args.function_name)
            ):
                continue
            if not contains(record.get("text"), args.query):
                continue
            matches.append(record)
            if len(matches) >= args.limit:
                break

    if args.format == "jsonl":
        for record in matches:
            print(json.dumps(record, ensure_ascii=False))
    else:
        if not matches:
            print("No matching phrasebank entries.")
        for record in matches:
            printed = record.get("printed_page")
            page = f"PDF {record['pdf_page']}" + (f", printed {printed}" if printed is not None else "")
            print(f"- **{record['section']} / {record['subheading']}** ({page})")
            print(f"  {record['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
