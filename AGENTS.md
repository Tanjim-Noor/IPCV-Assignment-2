# Repository Guidance

**Goal:** Develop a reproducible computer-vision system that detects, segments, and recognises university attire, then evaluates dress-code compliance.

**Intent:** Organise the work from dataset selection through experimentation, evaluation, demonstration, and an evidence-based final report.

## Authoritative sources

Treat `Assignment Requirements/CT103-3-M-IPCV Assignment - Part 2 (APUMF2604AI).pdf` as the primary brief and `Assignment Requirements/assignment-2-requirements.md` as its working, consolidated checklist with the lecturer's Teams clarification.

## Mandatory method constraint

- Deep learning is strictly prohibited in every phase, including preprocessing, feature extraction, detection, segmentation, recognition, evaluation, and inference.
- Do not use CNNs, RNNs, autoencoders, transformers, YOLO, U-Net, Mask R-CNN, SAM, CLIP, deep embeddings, pretrained deep features, hosted deep-learning APIs, or deep-learning components hidden behind a library call.
- Any non-deep-learning library or package is allowed. Prefer classical image processing and conventional machine learning such as colour/texture/shape features, HOG, SIFT/ORB, thresholding, morphology, contours, watershed/GrabCut, clustering, PCA, SVM, k-NN, random forests, or boosting.
- Check the underlying method of every dependency before adopting it. If a technique may rely on deep learning, do not use it unless the lecturer explicitly confirms it is permitted in writing.

## Repository map

- `Assignment Requirements/`: source brief, consolidated requirements, and source images.
- `implementation/data/`: dataset metadata and local raw, interim, processed, and test data.
- `implementation/stages/`: numbered Jupyter notebooks; run them in numeric order.
- `implementation/src/`: reusable Python code extracted from notebooks.
- `implementation/models/`: local model weights and checkpoints.
- `implementation/outputs/`: figures, metrics, and predictions used for evaluation or reporting.
- `report/sections/`: working report sections.
- `report/final-report.md`: assembled Markdown report.
- `report/output/`: final Word export, eventually `final-report.docx`.

## Working rules

- Keep raw data immutable. Record each dataset's source, licence, class definitions, and download date in `implementation/data/README.md` before use.
- Keep notebooks reproducible, numbered, and runnable from top to bottom. Move reusable logic into `implementation/src/`.
- Keep the complete implementation classical and auditable; document handcrafted features, algorithms, parameters, and decision rules.
- Save report-ready evidence under `implementation/outputs/`; do not use screenshots when an exported figure or table is available.
- Write sections in `report/sections/`, then assemble and reconcile them in `report/final-report.md`.
- Cite external datasets, code, methods, models, and text in APA style. Never present third-party or AI-assisted work as solely your own.
- Do not commit downloaded datasets, credentials, caches, checkpoints, or large model weights.

## Git change and commit-message protocol

Before and after every repository change:

1. Run `git status --short`.
2. Review unstaged changes with `git diff --`.
3. Review staged changes with `git diff --cached --`.
4. Preserve unrelated user changes and never stage or commit unless explicitly asked.

After making changes, always provide a copy-pasteable commit message in a fenced text block. Use an imperative subject and grouped or nested bullets when the change spans multiple areas, for example:

```text
docs: scaffold the IPCV assignment workspace

- Requirements:
  - Consolidate the brief and lecturer clarifications
  - Add a submission compliance checklist
- Workflow:
  - Add staged notebooks and report section templates
```
