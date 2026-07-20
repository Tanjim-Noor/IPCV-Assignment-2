#!/usr/bin/env python3
"""Add stable block markers and hashes to a Markdown draft."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


MARKER_RE = re.compile(r"^<!--block:(B\d{4,}) hash:([0-9a-f]{64})-->$")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_blocks(text: str) -> list[tuple[str | None, str]]:
    blocks: list[tuple[str | None, str]] = []
    current_id: str | None = None
    current: list[str] = []
    for chunk in re.split(r"\n{2,}", text.strip()):
        lines = chunk.splitlines()
        marker = MARKER_RE.match(lines[0].strip()) if lines else None
        if marker:
            current_id = marker.group(1)
            body = "\n".join(lines[1:]).strip()
        else:
            current_id = None
            body = chunk.strip()
        if body:
            blocks.append((current_id, body))
    return blocks


def canonical_text(blocks: list[tuple[str | None, str]]) -> str:
    return "\n\n".join(body for _, body in blocks).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    blocks = split_blocks(args.input.read_text(encoding="utf-8"))
    used = {block_id for block_id, _ in blocks if block_id}
    next_number = 1
    anchored: list[str] = []
    records: list[dict] = []
    for existing_id, body in blocks:
        block_id = existing_id
        while not block_id:
            candidate = f"B{next_number:04d}"
            next_number += 1
            if candidate not in used:
                block_id = candidate
                used.add(candidate)
        block_hash = digest(body)
        anchored.append(f"<!--block:{block_id} hash:{block_hash}-->\n{body}")
        records.append({"block_id": block_id, "hash": block_hash, "characters": len(body)})

    output_text = "\n\n".join(anchored).rstrip() + "\n"
    if args.output:
        args.output.write_text(output_text, encoding="utf-8", newline="\n")
    else:
        print(output_text, end="")
    if args.manifest:
        args.manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "base_sha256": digest(canonical_text(blocks)),
                    "blocks": records,
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

