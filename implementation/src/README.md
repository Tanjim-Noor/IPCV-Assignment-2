# Reusable Source Code

Move stable, reusable logic out of notebooks and into this directory. Organise modules around actual implementation needs after the dataset and methods are selected, such as data loading, preprocessing, detection, segmentation, recognition, compliance rules, evaluation, and visualisation.

Keep notebook code focused on experiment configuration, execution, and interpretation. Add docstrings and comments where they explain non-obvious reasoning.

## Dataset policy utilities

`ipcv_attire.dataset_policy` validates Fashionpedia annotations, derives compliance-relevant labels, creates duplicate-group-aware splits, produces local image and annotation manifests, and blocks unapproved images from presentation code.

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

`ipcv_attire.compliance` exposes the auditable `COMPLIANT`, `NON_COMPLIANT`, and `REVIEW_REQUIRED` interface. It combines explicit rule results only; it does not contain a learned model.

Run the standard-library tests with:

```powershell
python -m unittest discover implementation/tests -v
```
