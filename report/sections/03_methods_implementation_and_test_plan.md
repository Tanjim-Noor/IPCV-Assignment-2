# Methods, Implementation, and Test Plan

**Suggested length:** 900-1,050 words.

## Dataset and annotation strategy

Describe the selected dataset, licence, relevant classes or attributes, data preparation, split strategy, leakage controls, imbalance, and mapping to the university dress-code rules. Cite the dataset.

Fashionpedia 2020 is the primary component-training and in-domain evaluation source. Its instance masks and localized attributes support garment localization, segmentation, and recognition without requiring a deep method. The complete metadata is audited, but only annotations mapped to supported dress-code targets enter feature extraction. Training-only images are not manually content-filtered; all reproduced images must pass a separate university-safe whitelist. The official labelled validation split remains locked, while an independently captured, consented, deidentified university-context set provides external-domain evaluation.

Derived targets cover collared tops, allowed sleeve lengths, round-neck casual tops, revealing tops, formal-bottom candidates, casual or tight bottoms, damaged bottoms, footwear presence, and headwear presence. Unsupported or ambiguous conditions produce a review-required result rather than a guessed binary decision.

## Proposed pipeline

Explain the end-to-end data flow from input image to detection, segmentation, recognition, and compliance output. Include a labelled pipeline diagram when available.

_[Draft text and figure]_

## Detection and segmentation

Explain the selected methods, theoretical basis, implementation, parameters, and suitability for locating people or garments and segmenting attire. Compare with at least one credible alternative and justify the choice.

_[Draft text]_

## Recognition and compliance decision

Explain how garments or relevant attributes are recognised and how predictions map to transparent dress-code outcomes. Describe confidence/uncertainty handling and avoid unsupported inference of sensitive characteristics.

_[Draft text]_

## Implementation details

Record the Python environment, important libraries and versions, hardware, reproducibility controls, training configuration, and the relationship between notebooks and reusable source modules.

Full feature extraction, classical model fitting, and cross-validation run on a 32 GB desktop. Cached handcrafted features use batched `float32` storage under ignored data directories. The final CPU-compatible inference path is tested on the laptop used for the ScreenCam demonstration. Exact library versions, random seeds, hardware, elapsed time, and peak memory will be recorded for each reported experiment.

## Test plan

Define the test data, baselines, metrics, expected outputs, success criteria, and qualitative cases before presenting results. Cover detection, segmentation, recognition, final compliance, and relevant difficult conditions.

| Component | Test data | Output | Metric/validation | Success criterion |
| --- | --- | --- | --- | --- |
| Detection | Locked Fashionpedia validation and 100 university images | Garment/person boxes | Precision, recall, and AP at stated IoU thresholds | Exceed the fixed classical baseline and report class-level failures |
| Segmentation | Fashionpedia masks and 30 manually masked university images | Top, bottom, footwear, and headwear masks | IoU and Dice by class | Exceed the simplest threshold/morphology baseline and disclose domain loss |
| Recognition | Relevant Fashionpedia instances and university rule labels | Garment/attribute predictions | Macro-F1, balanced accuracy, and confusion matrices | Exceed majority prediction and report unsupported classes separately |
| Compliance | Locked in-domain and external test sets | Compliant, non-compliant, or review-required | Macro-F1, decidable-case accuracy, and review coverage | No forced decisions for missing or unsupported evidence; compare both domains |
