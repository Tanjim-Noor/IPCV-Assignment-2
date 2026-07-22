"""Evaluate a frozen model bundle on the locked Fashionpedia validation split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ipcv_attire.dataset_policy import load_policy
from ipcv_attire.evaluation import evaluate_locked_test
from ipcv_attire.pipeline import AttirePipeline


def main() -> None:
    implementation = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle-dir",
        type=Path,
        default=implementation / "models" / "classical-attire-full",
    )
    parser.add_argument("--maximum-images", type=int)
    parser.add_argument(
        "--output",
        type=Path,
        default=implementation / "outputs" / "metrics" / "locked-test-metrics.json",
    )
    args = parser.parse_args()
    policy_path = implementation / "data" / "dataset-policy.json"
    fashionpedia = implementation / "data" / "raw" / "fashionpedia"
    metrics = evaluate_locked_test(
        AttirePipeline.load(args.bundle_dir),
        image_manifest=implementation / "data" / "interim" / "manifests" / "fashionpedia-images.csv",
        fashionpedia_root=fashionpedia,
        validation_annotations=fashionpedia / "annotations" / "instances_attributes_val2020.json",
        policy=load_policy(policy_path),
        maximum_images=args.maximum_images,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

