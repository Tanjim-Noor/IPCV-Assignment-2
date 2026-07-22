"""Run explained classical attire inference on one local image."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image

from ipcv_attire.dataset_policy import require_showcase_approval
from ipcv_attire.pipeline import AttirePipeline
from ipcv_attire.visualization import render_report_overlay


def main() -> None:
    implementation = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument(
        "--bundle-dir",
        type=Path,
        default=implementation / "models" / "classical-attire-full",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=implementation / "outputs" / "predictions" / "single-image",
    )
    args = parser.parse_args()
    fashionpedia_root = (implementation / "data" / "raw" / "fashionpedia").resolve()
    input_path = args.image.resolve()
    try:
        relative = input_path.relative_to(fashionpedia_root).as_posix()
    except ValueError:
        relative = None
    if relative is not None:
        manifest = implementation / "data" / "interim" / "manifests" / "fashionpedia-images.csv"
        if not manifest.is_file():
            raise PermissionError(
                "Fashionpedia rendering is blocked until the dataset manifest exists."
            )
        with manifest.open(encoding="utf-8", newline="") as handle:
            record = next(
                (row for row in csv.DictReader(handle) if row["relative_image_path"] == relative),
                None,
            )
        if record is None:
            raise PermissionError("The Fashionpedia image is not present in the audited manifest.")
        require_showcase_approval(
            record["image_id"],
            implementation / "data" / "showcase-manifest.csv",
            display_risk=record["display_risk"] == "1",
        )
    pipeline = AttirePipeline.load(args.bundle_dir)
    report, prepared = pipeline.analyze_with_stages(args.image)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.output_dir / f"{args.image.stem}-report.json"
    overlay_path = args.output_dir / f"{args.image.stem}-overlay.png"
    report_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    Image.fromarray(render_report_overlay(prepared.normalized_rgb, report)).save(overlay_path)
    print(json.dumps({"report": str(report_path), "overlay": str(overlay_path), **report.to_dict()}, indent=2))


if __name__ == "__main__":
    main()
