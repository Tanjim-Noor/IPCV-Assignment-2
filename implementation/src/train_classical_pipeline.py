"""Train the Fashionpedia classical attire model bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ipcv_attire.dataset_policy import load_policy
from ipcv_attire.training import train_pipeline


def main() -> None:
    implementation = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "full"), default="smoke")
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=implementation / "data" / "interim" / "manifests",
    )
    parser.add_argument(
        "--fashionpedia-root",
        type=Path,
        default=implementation / "data" / "raw" / "fashionpedia",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=implementation / "data" / "dataset-policy.json",
    )
    parser.add_argument(
        "--bundle-dir",
        type=Path,
        default=None,
    )
    args = parser.parse_args()
    bundle_dir = args.bundle_dir or implementation / "models" / f"classical-attire-{args.profile}"
    output = train_pipeline(
        manifest_dir=args.manifest_dir,
        fashionpedia_root=args.fashionpedia_root,
        policy=load_policy(args.policy),
        bundle_dir=bundle_dir,
        profile_name=args.profile,
    )
    print(json.dumps({"model_bundle": str(output), "profile": args.profile}, indent=2))


if __name__ == "__main__":
    main()

