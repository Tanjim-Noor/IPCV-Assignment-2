"""CLI for generating local Fashionpedia manifests from immutable raw data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ipcv_attire.dataset_policy import build_manifest_bundle


def parse_args() -> argparse.Namespace:
    implementation_root = Path(__file__).resolve().parents[1]
    default_root = implementation_root / "data" / "raw" / "fashionpedia"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fashionpedia-root", type=Path, default=default_root)
    parser.add_argument(
        "--policy",
        type=Path,
        default=implementation_root / "data" / "dataset-policy.json",
    )
    parser.add_argument(
        "--showcase-manifest",
        type=Path,
        default=implementation_root / "data" / "showcase-manifest.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=implementation_root / "data" / "interim" / "manifests",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    annotations = args.fashionpedia_root / "annotations"
    summary = build_manifest_bundle(
        train_annotations=annotations / "instances_attributes_train2020.json",
        validation_annotations=annotations / "instances_attributes_val2020.json",
        fashionpedia_root=args.fashionpedia_root,
        policy_path=args.policy,
        output_dir=args.output_dir,
        showcase_manifest=args.showcase_manifest,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
