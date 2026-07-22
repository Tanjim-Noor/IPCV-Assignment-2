"""Render local contact sheets for manual Fashionpedia showcase review.

This script is deliberately separate from report/demo rendering. It may open
metadata-filtered but still unreviewed images, so it requires an explicit
acknowledgement and writes only to an ignored interim directory.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def parse_args() -> argparse.Namespace:
    implementation_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fashionpedia-root",
        type=Path,
        default=implementation_root / "data" / "raw" / "fashionpedia",
    )
    parser.add_argument(
        "--image-manifest",
        type=Path,
        default=implementation_root / "data" / "interim" / "manifests" / "fashionpedia-images.csv",
    )
    parser.add_argument(
        "--candidate-manifest",
        type=Path,
        default=implementation_root / "data" / "interim" / "manifests" / "showcase-candidates.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=implementation_root / "data" / "interim" / "showcase-review",
    )
    parser.add_argument("--per-sheet", type=int, default=20)
    parser.add_argument("--acknowledge-unreviewed-content", action="store_true")
    return parser.parse_args()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    args = parse_args()
    if not args.acknowledge_unreviewed_content:
        raise SystemExit(
            "Candidate images are not manually approved and may contain unsuitable content. "
            "Re-run with --acknowledge-unreviewed-content for private local review."
        )
    if args.per_sheet < 1:
        raise SystemExit("--per-sheet must be positive")

    try:
        from PIL import Image, ImageDraw, ImageOps
    except ImportError as error:
        raise SystemExit("Pillow is required to render review sheets") from error

    images = {row["image_id"]: row for row in _read_rows(args.image_manifest)}
    candidates = _read_rows(args.candidate_manifest)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    columns = 4
    cell_width, cell_height = 260, 340
    rows_per_sheet = math.ceil(args.per_sheet / columns)
    created: list[Path] = []
    for offset in range(0, len(candidates), args.per_sheet):
        batch = candidates[offset : offset + args.per_sheet]
        canvas = Image.new(
            "RGB",
            (columns * cell_width, rows_per_sheet * cell_height),
            "white",
        )
        draw = ImageDraw.Draw(canvas)
        for index, candidate in enumerate(batch):
            record = images[candidate["image_id"]]
            path = args.fashionpedia_root / record["relative_image_path"]
            with Image.open(path) as source:
                thumbnail = ImageOps.contain(source.convert("RGB"), (cell_width - 12, cell_height - 58))
            x = (index % columns) * cell_width + (cell_width - thumbnail.width) // 2
            y = (index // columns) * cell_height + 4
            canvas.paste(thumbnail, (x, y))
            label_y = (index // columns) * cell_height + cell_height - 50
            draw.text(
                ((index % columns) * cell_width + 6, label_y),
                f"PENDING REVIEW | ID {candidate['image_id']}",
                fill="black",
            )
            draw.text(
                ((index % columns) * cell_width + 6, label_y + 16),
                candidate.get("notes", "")[:42],
                fill="black",
            )
        output = args.output_dir / f"showcase-review-{offset // args.per_sheet + 1:02d}.jpg"
        canvas.save(output, quality=88)
        created.append(output)
    print(f"Created {len(created)} private review sheets in {args.output_dir}")


if __name__ == "__main__":
    main()
