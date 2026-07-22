# IPCV Assignment 2

Workspace for **University Professional Attire (Dress Code) Identification**, an individual Image Processing and Computer Vision assignment for intake APUMF2604AI.

## Start here

1. Read the [consolidated assignment requirements](<Assignment Requirements/assignment-2-requirements.md>).
2. Record dataset candidates and selection evidence in [the implementation data guide](implementation/data/README.md).
3. Run the notebooks in [implementation/stages](implementation/stages/) from stage 01 through stage 08.
4. Save figures, metrics, and example predictions in `implementation/outputs/`.
5. Draft individual sections in [report/sections](report/sections/) and assemble them in [report/final-report.md](report/final-report.md).
6. Export the completed report as `report/output/final-report.docx` using the required Word formatting.

## Main deliverables

- A functioning attire detection, segmentation, and recognition prototype.
- Commented source code and all relevant test images.
- A 10-15 minute individual ScreenCam demonstration.
- A 3,000-3,500 word report in Microsoft Word with APA citations.

The submission deadline stated in the brief is **11:59 pm, 9 August 2026**.

## Environment and notebook execution

Use the repository-local `.venv` for every Python and pip command. The Fashionpedia source dataset is intentionally excluded from Git, so place it under `implementation/data/raw/fashionpedia/` and complete the data register before running the stages.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\run_all_notebooks.py
```

The runner executes every numbered notebook in order with the repository root as its working directory, continues through later stages after a failure, and returns a non-zero exit code if any stage fails. It leaves source notebooks unchanged by default. Add `--write-results` only when execution counts and outputs should be saved into the notebooks. Use `--timeout 1800` for slow local cells if needed.

`requirements.txt` contains the direct runtime and notebook-execution dependencies. `requirements-lock.txt` records the exact Python 3.13 Windows environment used for this acceptance run.
