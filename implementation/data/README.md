# Dataset Register and Selection Template

Do not download data until its licence, relevance, and practical constraints have been reviewed. Keep downloaded data out of Git.

## Candidate comparison

| Candidate | Source URL | Licence | Images/subjects | Labels/annotations | Dress-code relevance | Main limitations | Decision |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| _To research_ |  |  |  |  |  |  |  |

## Selection criteria

- Contains full-body or sufficiently complete attire images.
- Supports detection, segmentation, and recognition directly or through defensible derived labels.
- Covers appropriate and inappropriate garment categories from the assignment brief.
- Has a licence that permits academic use and submission of derived work.
- Has sufficient label quality, class diversity, and sample size for evaluation.
- Provides enough demographic, pose, lighting, and background diversity to discuss bias and generalisation.
- Fits available storage, compute, and assignment time.
- Allows person-level or source-aware splitting to reduce train/test leakage.

## Selected dataset record

- **Name:** _Pending_
- **Version:** _Pending_
- **Source and citation:** _Pending_
- **Licence:** _Pending_
- **Download date:** _Pending_
- **Integrity check or archive hash:** _Pending_
- **Original classes and annotations:** _Pending_
- **Classes/attributes used in this project:** _Pending_
- **Mapping to dress-code rules:** _Pending_
- **Known limitations and bias risks:** _Pending_
- **Planned train/validation/test split:** _Pending_

## Data lifecycle

1. Place untouched source files in `raw/`.
2. Put validated, extracted, or relabelled data in `interim/`.
3. Put model-ready splits and generated annotations in `processed/`.
4. Put genuinely held-out or demonstration images in `test/`.
5. Record every transformation in the corresponding numbered notebook.
