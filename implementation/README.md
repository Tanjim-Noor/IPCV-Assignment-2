# Implementation Workspace

This directory keeps the dataset, staged experiments, reusable Python code, trained artifacts, and evidence for the report together. Fashionpedia 2020 is the sole source for training, validation, testing, and approved qualitative demonstrations. Results therefore measure performance within the Fashionpedia fashion-image domain, not on real university photographs.

## Recommended execution order

| Stage | Notebook | Main outcome |
| --- | --- | --- |
| 01 | Dataset selection | Defensible dataset choice, licence record, and acquisition plan |
| 02 | Data audit and EDA | Class, quality, leakage, and imbalance audit |
| 03 | Preprocessing and augmentation | Reproducible input and augmentation pipeline |
| 04 | Detection and segmentation | Localised people or garments and segmented attire regions |
| 05 | Recognition and compliance | Attire attributes/classes mapped to dress-code decisions |
| 06 | Training and tuning | Reproducible trained candidates and tuning evidence |
| 07 | Evaluation and error analysis | Quantitative validation and analysed failure cases |
| 08 | Inference and demo | End-to-end inference examples and ScreenCam-ready workflow |

Run the completed notebooks in numeric order. Notebook 08 is the standalone end-to-end demonstration and uses `TRAIN_IF_MISSING=True` with non-destructive train-if-missing behaviour.

## Environment and commands

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python implementation/src/build_dataset_manifests.py
python implementation/src/train_classical_pipeline.py --profile smoke
python implementation/src/infer_attire.py path\to\image.jpg --bundle-dir implementation/models/classical-attire-smoke
```

`requirements-lock.txt` records the exact laptop acceptance environment; use it when an exact Python 3.14 Windows reproduction is required.

For the final desktop run, replace `smoke` with `full`, then run:

```powershell
python implementation/src/evaluate_classical_pipeline.py --bundle-dir implementation/models/classical-attire-full
```

## Storage rules

- `data/raw/`: immutable downloaded Fashionpedia source data.
- `data/interim/`: validated, extracted, or relabelled intermediate data.
- `data/processed/`: model-ready splits and derived annotations.
- `data/test/`: held-out or demonstration inputs that are safe to retain locally.
- `src/`: reusable functions and modules moved out of notebooks.
- `models/`: local weights and checkpoints; these are ignored by Git.
- `outputs/figures/`: curated plots and qualitative examples for the report.
- `outputs/metrics/`: compact tables or machine-readable evaluation summaries.
- `outputs/predictions/`: potentially large generated predictions; ignored by Git by default.

Document data provenance before acquisition. The implementation must remain entirely classical: do not add deep models, pretrained deep features, auto-segmentation tools, or dependencies that hide deep-learning components.

## Compute roles

- Use the 32 GB desktop for full feature extraction, internal-validation tuning, and training.
- Keep cached features under ignored `data/interim/` or `data/processed/` paths as batched `float32` arrays.
- Keep a CPU-compatible inference path so the trained system and demonstration remain runnable on the laptop.
- Require at least 40 GB of desktop working space before full feature extraction.
- The RTX 3080 is not used: HOG, GrabCut, handcrafted features, linear SVMs, and SGD logistic models all run on CPU.
- The default 512-pixel maximum side bounds classical sliding-window cost while preserving aspect ratio.
