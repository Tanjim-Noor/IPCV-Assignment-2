# Implementation Workspace

This directory keeps the dataset, staged experiments, reusable Python code, trained artifacts, and evidence for the report together. No dataset or model architecture has been selected yet.

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

Each stage directory contains a starter notebook. Run them in numeric order and keep notebooks executable from top to bottom.

## Storage rules

- `data/raw/`: immutable downloaded or collected source data.
- `data/interim/`: validated, extracted, or relabelled intermediate data.
- `data/processed/`: model-ready splits and derived annotations.
- `data/test/`: held-out or demonstration inputs that are safe to retain locally.
- `src/`: reusable functions and modules moved out of notebooks.
- `models/`: local weights and checkpoints; these are ignored by Git.
- `outputs/figures/`: curated plots and qualitative examples for the report.
- `outputs/metrics/`: compact tables or machine-readable evaluation summaries.
- `outputs/predictions/`: potentially large generated predictions; ignored by Git by default.

Document data provenance before acquisition. Add dependencies only after the dataset and modelling approach are chosen so the environment reflects the actual implementation.
