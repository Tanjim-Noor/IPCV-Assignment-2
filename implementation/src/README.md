# Reusable Source Code

Move stable, reusable logic out of notebooks and into this directory. Organise modules around actual implementation needs after the dataset and methods are selected, such as data loading, preprocessing, detection, segmentation, recognition, compliance rules, evaluation, and visualisation.

Keep notebook code focused on experiment configuration, execution, and interpretation. Add docstrings and comments where they explain non-obvious reasoning.

## Dataset policy utilities

`ipcv_attire.dataset_policy` validates Fashionpedia annotations, derives compliance-relevant targets and image-level decisions, creates duplicate-group-aware splits, produces local image and annotation manifests, and blocks unapproved images from presentation code.

Generate the manifests after downloading Fashionpedia:

```powershell
python implementation/src/build_dataset_manifests.py
```

Generated CSV and JSON files are written to `implementation/data/interim/manifests/` and remain ignored by Git. Review `showcase-candidates.csv`, then copy only manually accepted IDs and their approval metadata into the tracked `implementation/data/showcase-manifest.csv`.

For private manual review, render contact sheets only after acknowledging that metadata-filtered candidates are not yet content-approved:

```powershell
python implementation/src/render_showcase_candidates.py --acknowledge-unreviewed-content
```

The sheets remain under ignored `data/interim/showcase-review/`. They are never report-ready by themselves.

Generated image manifests include the derived compliance label, prohibited rules found, and required evidence that is missing. The labelled Fashionpedia validation split is the locked quantitative test; unlabelled test images are qualitative-only and still require showcase approval.

`ipcv_attire.compliance` exposes the auditable `COMPLIANT`, `NON_COMPLIANT`, and `REVIEW_REQUIRED` interface. It combines explicit rule results only; it does not contain a learned model. `derive_compliance_label` applies the tracked Fashionpedia-supported rule set to annotation-derived targets.

## End-to-end classical API

`ipcv_attire.pipeline.AttirePipeline` joins deterministic preprocessing, four HOG-linear-SVM component detectors, GrabCut segmentation, handcrafted recognition features, uncertainty thresholds, outfit grouping, and complete rule explanations:

```python
from ipcv_attire import AttirePipeline

pipeline = AttirePipeline.load("implementation/models/classical-attire-full")
report = pipeline.analyze("input.jpg")
print(report.to_dict())
```

Train and evaluate from the repository root:

```powershell
python implementation/src/train_classical_pipeline.py --profile smoke
python implementation/src/train_classical_pipeline.py --profile full --bundle-dir implementation/models/classical-attire-full
python implementation/src/evaluate_classical_pipeline.py --bundle-dir implementation/models/classical-attire-full
```

The model bundle records its own SHA-256, policy SHA-256, environment, features, trained targets, profile, and thresholds. Models and float32 feature caches stay ignored. The full profile performs one hard-negative-mining pass; the smoke profile is an acceptance test, not report evidence.

Run the test suite with the project environment:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s implementation/tests -v
```
