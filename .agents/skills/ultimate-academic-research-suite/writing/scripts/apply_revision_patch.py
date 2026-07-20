#!/usr/bin/env python3
"""Apply verified block replacements to an anchorized Markdown draft."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


BLOCK_RE = re.compile(
    r"<!--block:(B\d{4,}) hash:([0-9a-f]{64})-->\n(.*?)(?=\n{2}<!--block:|\Z)",
    re.DOTALL,
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_blocks(text: str) -> list[dict]:
    blocks = []
    for match in BLOCK_RE.finditer(text.strip()):
        body = match.group(3).strip()
        declared = match.group(2)
        actual = digest(body)
        if actual != declared:
            raise ValueError(f"Hash mismatch in {match.group(1)}: declared {declared}, actual {actual}")
        blocks.append({"block_id": match.group(1), "hash": actual, "body": body})
    if not blocks:
        raise ValueError("No anchorized blocks found")
    return blocks


def canonical_text(blocks: list[dict]) -> str:
    return "\n\n".join(block["body"] for block in blocks).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path)
    parser.add_argument("patch", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    blocks = parse_blocks(args.draft.read_text(encoding="utf-8"))
    patch = json.loads(args.patch.read_text(encoding="utf-8"))
    base_hash = digest(canonical_text(blocks))
    if patch.get("base_sha256") != base_hash:
        raise SystemExit(
            f"Base draft hash mismatch: patch={patch.get('base_sha256')} actual={base_hash}"
        )
    by_id = {block["block_id"]: block for block in blocks}
    changes: list[dict] = []
    seen: set[str] = set()
    for item in patch.get("patches", []):
        block_id = item["block_id"]
        if block_id in seen:
            raise SystemExit(f"Duplicate patch for {block_id}")
        seen.add(block_id)
        if block_id not in by_id:
            raise SystemExit(f"Unknown block: {block_id}")
        block = by_id[block_id]
        if item["old_hash"] != block["hash"]:
            raise SystemExit(f"Old hash mismatch for {block_id}")
        replacement = item["replacement"].strip()
        if not replacement:
            raise SystemExit(f"Empty replacement for {block_id}; deletion is intentionally unsupported")
        new_hash = digest(replacement)
        changes.append(
            {
                "block_id": block_id,
                "old_hash": block["hash"],
                "new_hash": new_hash,
                "changed": replacement != block["body"],
            }
        )
        block["body"] = replacement
        block["hash"] = new_hash

    output = "\n\n".join(
        f"<!--block:{block['block_id']} hash:{block['hash']}-->\n{block['body']}" for block in blocks
    ).rstrip() + "\n"
    args.output.write_text(output, encoding="utf-8", newline="\n")
    if args.report:
        args.report.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "base_sha256": base_hash,
                    "result_sha256": digest(canonical_text(blocks)),
                    "changed_blocks": changes,
                    "untouched_blocks": [
                        block["block_id"] for block in blocks if block["block_id"] not in seen
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

