"""Fashionpedia audit, label derivation, split, and showcase utilities.

All operations are metadata-driven or conventional file processing. The module
does not call a pretrained model, hosted service, or deep-learning library.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Sequence


MANIFEST_FIELDS = (
    "image_id",
    "source",
    "raw_split",
    "final_split",
    "file_name",
    "relative_image_path",
    "original_url",
    "license_id",
    "width",
    "height",
    "duplicate_group",
    "category_names",
    "attribute_names",
    "derived_targets",
    "compliance_label",
    "failed_rules",
    "missing_required_rules",
    "relevant",
    "display_risk",
    "showcase_status",
)

ANNOTATION_FIELDS = (
    "annotation_id",
    "image_id",
    "raw_split",
    "final_split",
    "category_id",
    "category_name",
    "attribute_ids",
    "attribute_names",
    "bbox",
    "area",
    "iscrowd",
    "derived_targets",
    "relevant",
    "display_risk",
)


def load_policy(path: str | Path) -> dict[str, Any]:
    """Load and minimally validate the tracked dataset policy."""

    policy_path = Path(path)
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    required = {
        "policy_version",
        "categories",
        "attributes",
        "derived_targets",
        "compliance_rules",
        "pipeline",
        "showcase",
    }
    missing = required - policy.keys()
    if missing:
        raise ValueError(f"Dataset policy is missing keys: {sorted(missing)}")
    known_targets = set(policy["derived_targets"])
    required_targets = set(policy["compliance_rules"]["required_evidence"])
    prohibited_targets = set(policy["compliance_rules"]["prohibited_evidence"])
    unknown_targets = (required_targets | prohibited_targets) - known_targets
    if unknown_targets:
        raise ValueError(f"Compliance rules reference unknown targets: {sorted(unknown_targets)}")
    overlap = required_targets & prohibited_targets
    if overlap:
        raise ValueError(f"Compliance targets cannot be both required and prohibited: {sorted(overlap)}")
    definitions = policy["compliance_rules"].get("rule_definitions", {})
    missing_definitions = known_targets - definitions.keys()
    if missing_definitions:
        raise ValueError(
            f"Derived targets are missing rule definitions: {sorted(missing_definitions)}"
        )
    recognition_targets = {
        target
        for targets in policy["pipeline"].get("recognition_targets", {}).values()
        for target in targets
    }
    unknown_recognition = recognition_targets - known_targets
    if unknown_recognition:
        raise ValueError(
            f"Recognition configuration references unknown targets: {sorted(unknown_recognition)}"
        )
    return policy


def validate_annotation_data(data: Mapping[str, Any]) -> dict[str, int]:
    """Validate the COCO-style links used by Fashionpedia annotations."""

    required = {"images", "annotations", "categories", "attributes"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Annotation document is missing keys: {sorted(missing)}")

    image_ids = [int(image["id"]) for image in data["images"]]
    category_ids = [int(category["id"]) for category in data["categories"]]
    attribute_ids = [int(attribute["id"]) for attribute in data["attributes"]]
    if len(image_ids) != len(set(image_ids)):
        raise ValueError("Duplicate image IDs found")
    if len(category_ids) != len(set(category_ids)):
        raise ValueError("Duplicate category IDs found")
    if len(attribute_ids) != len(set(attribute_ids)):
        raise ValueError("Duplicate attribute IDs found")

    known_images = set(image_ids)
    known_categories = set(category_ids)
    known_attributes = set(attribute_ids)
    bad_image_links = 0
    bad_category_links = 0
    bad_attribute_links = 0
    invalid_boxes = 0
    for annotation in data["annotations"]:
        bad_image_links += int(int(annotation["image_id"]) not in known_images)
        bad_category_links += int(int(annotation["category_id"]) not in known_categories)
        bad_attribute_links += sum(
            int(int(attribute_id) not in known_attributes)
            for attribute_id in annotation.get("attribute_ids", [])
        )
        bbox = annotation.get("bbox", [])
        invalid_boxes += int(len(bbox) != 4 or (len(bbox) == 4 and (bbox[2] <= 0 or bbox[3] <= 0)))

    if bad_image_links or bad_category_links or bad_attribute_links:
        raise ValueError(
            "Invalid annotation graph: "
            f"image_links={bad_image_links}, category_links={bad_category_links}, "
            f"attribute_links={bad_attribute_links}"
        )
    return {
        "images": len(image_ids),
        "annotations": len(data["annotations"]),
        "categories": len(category_ids),
        "attributes": len(attribute_ids),
        "invalid_zero_area_boxes": invalid_boxes,
    }


def _has_valid_bbox(annotation: Mapping[str, Any]) -> bool:
    bbox = annotation.get("bbox", [])
    return len(bbox) == 4 and bbox[2] > 0 and bbox[3] > 0


def derive_targets(
    category_name: str,
    attribute_names: Iterable[str],
    policy: Mapping[str, Any],
) -> dict[str, bool]:
    """Derive auditable task labels for one annotated garment instance."""

    attributes = set(attribute_names)
    category_groups = policy["categories"]
    attribute_groups = policy["attributes"]
    upper = category_name in set(category_groups["upper_body"])
    bottoms = category_name in set(category_groups["bottom_body"])
    collar_region = category_name == "collar"
    sleeve_region = category_name == "sleeve"
    neckline_region = category_name == "neckline"
    casual_bottom_attributes = set(attribute_groups["casual_bottoms"])
    formal_bottom_exclusions = set(attribute_groups["formal_bottom_exclusions"])

    targets = {
        "collared_top": (upper or collar_region)
        and bool(attributes & set(attribute_groups["collars"])),
        "allowed_sleeve": (upper or sleeve_region)
        and bool(attributes & set(attribute_groups["allowed_sleeves"])),
        "casual_round_neck_top": (upper or neckline_region)
        and bool(attributes & set(attribute_groups["casual_round_neck_tops"])),
        "revealing_top": (upper or neckline_region or sleeve_region)
        and bool(attributes & set(attribute_groups["revealing_tops"])),
        "formal_bottom_candidate": category_name == "pants"
        and not bool(attributes & formal_bottom_exclusions),
        "casual_or_tight_bottom": (
            category_name == "tights, stockings"
            or (bottoms and bool(attributes & casual_bottom_attributes))
        ),
        "damaged_bottom": bottoms
        and bool(attributes & set(attribute_groups["damaged_bottoms"])),
        "skort_bottom": category_name == "shorts"
        and bool(attributes & set(attribute_groups["skorts"])),
        "leisurewear": bool(attributes & set(attribute_groups["leisurewear"])),
        "footwear_present": category_name in set(category_groups["footwear"]),
        "headwear_present": category_name in set(category_groups["headwear"]),
    }
    expected = set(policy["derived_targets"])
    if set(targets) != expected:
        raise ValueError("Policy target names do not match the implemented target derivation")
    return targets


def derive_compliance_label(
    derived_targets: Iterable[str],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive an auditable image-level label from Fashionpedia-supported targets.

    Prohibited evidence takes precedence. An image is compliant only when all
    required proxy evidence is present and no prohibited target is present.
    Everything else remains review-required rather than being guessed.
    """

    present = set(derived_targets)
    known = set(policy["derived_targets"])
    unknown = present - known
    if unknown:
        raise ValueError(f"Cannot evaluate unknown derived targets: {sorted(unknown)}")

    rules = policy["compliance_rules"]
    required = list(rules["required_evidence"])
    prohibited = list(rules["prohibited_evidence"])
    failed = [target for target in prohibited if target in present]
    missing = [target for target in required if target not in present]

    if failed:
        label = "non_compliant"
    elif not missing:
        label = "compliant"
    else:
        label = "review_required"
    return {
        "compliance_label": label,
        "failed_rules": failed,
        "missing_required_rules": missing,
    }


def _duplicate_group(image: Mapping[str, Any]) -> str:
    source = str(image.get("original_url") or "").strip().lower()
    if not source:
        source = f"file:{image.get('file_name', image['id'])}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]


def _relative_image_path(file_name: str, raw_split: str) -> str:
    directory = "train" if raw_split == "official_train" else "test"
    return f"images/{directory}/{Path(file_name).name}"


def _annotation_records(
    data: Mapping[str, Any],
    raw_split: str,
    policy: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[int, dict[str, set[str]]]]:
    category_names = {int(item["id"]): str(item["name"]) for item in data["categories"]}
    attribute_names = {int(item["id"]): str(item["name"]) for item in data["attributes"]}
    display_risk_names = set(policy["attributes"]["display_risk"])
    image_aggregates: dict[int, dict[str, set[str]]] = defaultdict(
        lambda: {"categories": set(), "attributes": set(), "targets": set()}
    )
    records: list[dict[str, Any]] = []
    for annotation in data["annotations"]:
        # Fashionpedia train contains a small number of zero-area decoration
        # annotations. Keep the source immutable, record their count in the
        # audit summary, and exclude them from all model-ready manifests.
        if not _has_valid_bbox(annotation):
            continue
        image_id = int(annotation["image_id"])
        category_id = int(annotation["category_id"])
        attribute_ids = [int(value) for value in annotation.get("attribute_ids", [])]
        category_name = category_names[category_id]
        names = [attribute_names[value] for value in attribute_ids]
        target_flags = derive_targets(category_name, names, policy)
        targets = sorted(name for name, enabled in target_flags.items() if enabled)
        relevant = bool(targets)
        display_risk = bool(set(names) & display_risk_names)
        record = {
            "annotation_id": int(annotation["id"]),
            "image_id": image_id,
            "raw_split": raw_split,
            "final_split": "",
            "category_id": category_id,
            "category_name": category_name,
            "attribute_ids": attribute_ids,
            "attribute_names": sorted(names),
            "bbox": annotation.get("bbox", []),
            "area": annotation.get("area"),
            "iscrowd": int(annotation.get("iscrowd", 0)),
            "derived_targets": targets,
            "relevant": relevant,
            "display_risk": display_risk,
        }
        records.append(record)
        aggregate = image_aggregates[image_id]
        aggregate["categories"].add(category_name)
        aggregate["attributes"].update(names)
        aggregate["targets"].update(targets)
    return records, image_aggregates


def _image_records(
    data: Mapping[str, Any],
    raw_split: str,
    aggregates: Mapping[int, Mapping[str, set[str]]],
    policy: Mapping[str, Any],
) -> list[dict[str, Any]]:
    display_risk_names = set(policy["attributes"]["display_risk"])
    records: list[dict[str, Any]] = []
    for image in data["images"]:
        image_id = int(image["id"])
        aggregate = aggregates.get(
            image_id,
            {"categories": set(), "attributes": set(), "targets": set()},
        )
        attributes = sorted(aggregate["attributes"])
        targets = sorted(aggregate["targets"])
        compliance = derive_compliance_label(targets, policy)
        records.append(
            {
                "image_id": image_id,
                "source": "fashionpedia",
                "raw_split": raw_split,
                "final_split": "locked_in_domain_test"
                if raw_split == "official_validation"
                else "",
                "file_name": Path(str(image["file_name"])).name,
                "relative_image_path": _relative_image_path(str(image["file_name"]), raw_split),
                "original_url": str(image.get("original_url") or ""),
                "license_id": image.get("license", ""),
                "width": int(image.get("width", 0)),
                "height": int(image.get("height", 0)),
                "duplicate_group": _duplicate_group(image),
                "category_names": sorted(aggregate["categories"]),
                "attribute_names": attributes,
                "derived_targets": targets,
                **compliance,
                "relevant": bool(aggregate["targets"]),
                "display_risk": bool(set(attributes) & display_risk_names),
                "showcase_status": "",
            }
        )
    return records


def _assign_grouped_stratified_split(
    records: Sequence[MutableMapping[str, Any]],
    validation_fraction: float,
    seed: int,
) -> dict[int, str]:
    """Assign duplicate groups within multi-label signature buckets."""

    groups: dict[str, list[MutableMapping[str, Any]]] = defaultdict(list)
    for record in records:
        groups[str(record["duplicate_group"])].append(record)

    signature_buckets: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for group_id, members in groups.items():
        signature = tuple(sorted({target for item in members for target in item["derived_targets"]}))
        signature_buckets[signature].append(group_id)

    assignments: dict[int, str] = {}
    for signature, group_ids in signature_buckets.items():
        ordered = sorted(
            group_ids,
            key=lambda value: hashlib.sha256(f"{seed}:{signature}:{value}".encode()).hexdigest(),
        )
        validation_count = round(len(ordered) * validation_fraction)
        if len(ordered) >= 5:
            validation_count = max(1, validation_count)
        validation_groups = set(ordered[:validation_count])
        for group_id in ordered:
            split = "internal_validation" if group_id in validation_groups else "train"
            for record in groups[group_id]:
                record["final_split"] = split
                assignments[int(record["image_id"])] = split
    return assignments


def _write_csv(path: Path, fieldnames: Sequence[str], records: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for source in records:
            record = dict(source)
            for key, value in list(record.items()):
                if isinstance(value, (list, dict, tuple)):
                    record[key] = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                elif isinstance(value, bool):
                    record[key] = int(value)
            writer.writerow(record)


def _load_showcase_statuses(path: Path, valid_statuses: set[str]) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle)
        statuses: dict[str, str] = {}
        for row in rows:
            image_id = str(row.get("image_id") or "").strip()
            status = str(row.get("status") or "").strip()
            if not image_id:
                continue
            if status not in valid_statuses:
                raise ValueError(f"Invalid showcase status {status!r} for image {image_id}")
            statuses[image_id] = status
        return statuses


def require_showcase_approval(
    image_id: str | int,
    showcase_manifest: str | Path,
    *,
    display_risk: bool,
) -> None:
    """Fail closed unless an image is both low-risk and explicitly approved."""

    if display_risk:
        raise PermissionError(
            f"Fashionpedia image {image_id} is display-risk flagged; rendering is blocked."
        )

    path = Path(showcase_manifest)
    statuses = _load_showcase_statuses(
        path,
        {
            "pending",
            "approved",
            "rejected_content",
            "rejected_quality",
            "rejected_domain",
            "rejected_rights",
            "rejected_ambiguous_age",
        },
    )
    if statuses.get(str(image_id)) != "approved":
        raise PermissionError(
            f"Fashionpedia image {image_id} is not approved in {path}; rendering is blocked."
        )


def _candidate_records(
    image_records: Sequence[Mapping[str, Any]],
    candidate_count: int,
    seed: int,
) -> list[dict[str, Any]]:
    eligible = [
        record
        for record in image_records
        if record["relevant"] and not record["display_risk"] and record["derived_targets"]
    ]
    buckets: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in eligible:
        for target in record["derived_targets"]:
            if target != "revealing_top":
                buckets[target].append(record)

    selected: dict[str, dict[str, Any]] = {}
    target_order = sorted(buckets)
    per_target = max(1, candidate_count // max(1, len(target_order)))
    for target in target_order:
        ordered = sorted(
            buckets[target],
            key=lambda record: hashlib.sha256(
                f"{seed}:{target}:{record['image_id']}".encode()
            ).hexdigest(),
        )
        for record in ordered[:per_target]:
            selected[str(record["image_id"])] = {
                "image_id": record["image_id"],
                "status": "pending",
                "reason": "",
                "notes": f"candidate targets: {', '.join(record['derived_targets'])}",
                "approved_by": "",
                "approved_at": "",
            }
    return list(selected.values())[:candidate_count]


def _add_unlabelled_test_images(
    image_records: list[dict[str, Any]],
    fashionpedia_root: Path,
) -> int:
    test_dir = fashionpedia_root / "images" / "test"
    if not test_dir.exists():
        return 0
    known = {str(record["file_name"]).lower() for record in image_records}
    added = 0
    next_id = -1
    for path in sorted(test_dir.glob("*")):
        if not path.is_file() or path.name.lower() in known:
            continue
        image_records.append(
            {
                "image_id": next_id,
                "source": "fashionpedia",
                "raw_split": "official_test_unlabelled",
                "final_split": "qualitative_only_unlabelled",
                "file_name": path.name,
                "relative_image_path": f"images/test/{path.name}",
                "original_url": "",
                "license_id": "",
                "width": 0,
                "height": 0,
                "duplicate_group": hashlib.sha256(f"file:{path.name}".encode()).hexdigest()[:20],
                "category_names": [],
                "attribute_names": [],
                "derived_targets": [],
                "compliance_label": "",
                "failed_rules": [],
                "missing_required_rules": [],
                "relevant": False,
                "display_risk": False,
                "showcase_status": "",
            }
        )
        next_id -= 1
        added += 1
    return added


def build_manifest_bundle(
    *,
    train_annotations: str | Path,
    validation_annotations: str | Path,
    fashionpedia_root: str | Path,
    policy_path: str | Path,
    output_dir: str | Path,
    showcase_manifest: str | Path | None = None,
) -> dict[str, Any]:
    """Validate Fashionpedia and write reproducible image/instance manifests."""

    policy = load_policy(policy_path)
    root = Path(fashionpedia_root)
    output = Path(output_dir)
    train_data = json.loads(Path(train_annotations).read_text(encoding="utf-8"))
    validation_data = json.loads(Path(validation_annotations).read_text(encoding="utf-8"))
    validation = {
        "train": validate_annotation_data(train_data),
        "validation": validate_annotation_data(validation_data),
    }

    train_annotations_records, train_aggregates = _annotation_records(
        train_data, "official_train", policy
    )
    validation_annotation_records, validation_aggregates = _annotation_records(
        validation_data, "official_validation", policy
    )
    train_image_records = _image_records(
        train_data, "official_train", train_aggregates, policy
    )
    validation_image_records = _image_records(
        validation_data, "official_validation", validation_aggregates, policy
    )
    split_assignments = _assign_grouped_stratified_split(
        train_image_records,
        float(policy["internal_validation_fraction"]),
        int(policy["split_seed"]),
    )
    for annotation in train_annotations_records:
        annotation["final_split"] = split_assignments[int(annotation["image_id"])]
    for annotation in validation_annotation_records:
        annotation["final_split"] = "locked_in_domain_test"

    image_records = train_image_records + validation_image_records
    unlabelled_test_images = _add_unlabelled_test_images(image_records, root)
    missing_image_files = [
        str(root / record["relative_image_path"])
        for record in image_records
        if not (root / record["relative_image_path"]).is_file()
    ]
    if missing_image_files:
        examples = ", ".join(missing_image_files[:5])
        raise FileNotFoundError(
            f"{len(missing_image_files)} manifest images are missing; examples: {examples}"
        )
    valid_showcase_statuses = set(policy["showcase"]["valid_statuses"])
    statuses = (
        _load_showcase_statuses(Path(showcase_manifest), valid_showcase_statuses)
        if showcase_manifest
        else {}
    )
    for record in image_records:
        record["showcase_status"] = statuses.get(str(record["image_id"]), "")

    annotation_records = train_annotations_records + validation_annotation_records
    _write_csv(output / "fashionpedia-images.csv", MANIFEST_FIELDS, image_records)
    _write_csv(
        output / "fashionpedia-annotations.csv",
        ANNOTATION_FIELDS,
        annotation_records,
    )
    candidates = _candidate_records(
        image_records,
        int(policy["showcase"]["candidate_count"]),
        int(policy["split_seed"]),
    )
    _write_csv(
        output / "showcase-candidates.csv",
        ("image_id", "status", "reason", "notes", "approved_by", "approved_at"),
        candidates,
    )

    target_image_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for record in image_records:
        for target in record["derived_targets"]:
            target_image_counts[target][record["final_split"]] += 1
    minimum_train = int(policy["minimum_support"]["training_positive_images"])
    minimum_test = int(policy["minimum_support"]["locked_validation_positive_images"])
    support = {
        target: {
            "train": counts["train"],
            "internal_validation": counts["internal_validation"],
            "locked_in_domain_test": counts["locked_in_domain_test"],
            "standalone_supported": counts["train"] >= minimum_train
            and counts["locked_in_domain_test"] >= minimum_test,
        }
        for target, counts in sorted(target_image_counts.items())
    }
    summary = {
        "policy_version": policy["policy_version"],
        "validation": validation,
        "manifest_images": len(image_records),
        "manifest_annotations": len(annotation_records),
        "excluded_invalid_annotations": sum(
            split["invalid_zero_area_boxes"] for split in validation.values()
        ),
        "unlabelled_official_test_images": unlabelled_test_images,
        "missing_image_files": len(missing_image_files),
        "relevant_images": sum(bool(record["relevant"]) for record in image_records),
        "display_risk_images": sum(bool(record["display_risk"]) for record in image_records),
        "approved_showcase_images": sum(
            record["showcase_status"] == policy["showcase"]["approved_status"]
            for record in image_records
        ),
        "candidate_showcase_images": len(candidates),
        "compliance_labels": dict(
            sorted(
                Counter(
                    record["compliance_label"]
                    for record in image_records
                    if record["compliance_label"]
                ).items()
            )
        ),
        "target_support": support,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary
