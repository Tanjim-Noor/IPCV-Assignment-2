# Methods, Implementation, and Test Plan

**Suggested length:** 900-1,050 words.

## Dataset and annotation strategy

Describe the selected dataset, licence, relevant classes or attributes, data preparation, split strategy, leakage controls, imbalance, and mapping to the university dress-code rules. Cite the dataset.

Fashionpedia 2020 is the sole training and evaluation source. Its instance masks and localized attributes support garment localization, segmentation, and recognition without requiring a deep method. The complete metadata is audited, but only annotations mapped to supported dress-code targets enter feature extraction. Training images are not manually content-filtered; all reproduced images must pass both the metadata display-risk filter and a separate university-safe whitelist. The official training split supplies duplicate-group-separated training and internal validation partitions, while the official labelled validation split remains the locked final test. Unlabelled official test images are qualitative-only. No result is presented as validation on real university photographs.

Derived targets cover collared tops, allowed sleeve lengths, round-neck casual tops, revealing tops, formal-bottom candidates, casual or tight bottoms, damaged bottoms, skorts, leisurewear, footwear presence, and headwear presence. Prohibited evidence produces a non-compliant decision; complete required evidence with no prohibition produces compliant; missing or uncertain evidence produces review required. Tucked-in status, excessive piercings, exact open-toe footwear type, and customary-headgear exceptions are unsupported limitations rather than guessed decisions.

## Implemented pipeline

Explain the end-to-end data flow from input image to detection, segmentation, recognition, and compliance output. Include a labelled pipeline diagram when available.

The public interface loads an image path or array and returns an auditable report. Pillow performs decoding, EXIF correction, and RGB/RGBA/grayscale normalization. Aspect-ratio resizing bounds the maximum side at 512 pixels and CLAHE normalizes LAB luminance. Four HOG sliding-window linear-SVM detectors localize upper garments, bottoms, footwear, and headwear; per-class non-maximum suppression removes duplicate boxes. Horizontal overlap, centre distance, and vertical order associate components into outfits, with ambiguous assignments routed to review. GrabCut initializes from each box, followed by morphological opening/closing and largest-component filtering. Mask quality limits prevent empty or implausible masks from being treated as evidence. HOG, uniform LBP, HSV histograms, colour moments, edge density, and mask-shape statistics feed weighted target-specific SGD logistic classifiers. Low/high probability thresholds create an explicit uncertainty interval. Finally, every supported and unsupported rule is evaluated, per-outfit results are aggregated conservatively, and the report returns evidence IDs, reasons, timings, and warnings.

## Detection and segmentation

Explain the selected methods, theoretical basis, implementation, parameters, and suitability for locating people or garments and segmenting attire. Compare with at least one credible alternative and justify the choice.

Each detector uses Fashionpedia component boxes as positives and deterministic low-overlap crops as negatives. The full profile adds one hard-negative-mining pass. HOG and a linear SVM were chosen because their oriented-gradient representation and linear decision function are classical, inspectable, and CPU-compatible. A fixed centre-window detector is retained as the detection baseline. GrabCut uses colour Gaussian mixtures and graph cut within each detected rectangle; morphology removes speckle and the largest connected component supplies the final mask. Its comparison baseline is the unsegmented rectangular detection mask. Fashionpedia polygon and RLE masks are decoded with `pycocotools` only for ground-truth evaluation.

## Recognition and compliance decision

Explain how garments or relevant attributes are recognised and how predictions map to transparent dress-code outcomes. Describe confidence/uncertainty handling and avoid unsupported inference of sensitive characteristics.

The recognition models use only handcrafted evidence. A scaler and weighted SGD logistic classifier are fitted per target; a separate HOG-only classifier and a training-majority predictor provide recognition baselines. Thresholds are selected on internal validation to maximize macro-F1 among decided cases while retaining at least 80% coverage. Revealing tops, casual round necks, casual/tight or damaged bottoms, leisurewear, and headwear are immediate failures. Confident absence of a collar or permitted sleeve on a clearly visible upper garment also fails. Formal bottoms and footwear are documented proxies. Missing or uncertain evidence produces review required, and the rule engine continues after failures to report every reason. Skort recognition is unsupported because only five training examples exist. Tucked-in status, excessive piercings, exact open-toe subtype, and customary-headgear exceptions are always marked unsupported.

## Implementation details

Record the Python environment, important libraries and versions, hardware, reproducibility controls, training configuration, and the relationship between notebooks and reusable source modules.

Full feature extraction, classical model fitting, and internal-validation tuning run on a 32 GB desktop. Cached handcrafted features use disk-backed `float32` arrays under ignored data directories. The RTX 3080 is unused. The model bundle freezes the policy hash, artifact hash, feature parameters, package versions, detector and recognizer artifacts, fitted scalers, thresholds, and seed. A fixed-subset smoke profile validates the same CPU path on the laptop; only a completed full-profile locked test may supply final report metrics.

## Test plan

Define the test data, baselines, metrics, expected outputs, success criteria, and qualitative cases before presenting results. Cover detection, segmentation, recognition, final compliance, and relevant difficult conditions.

| Component | Test data | Output | Metric/validation | Success criterion |
| --- | --- | --- | --- | --- |
| Detection | Locked Fashionpedia labelled validation split | Garment/person boxes | Precision, recall, and AP at stated IoU thresholds | Exceed the fixed classical baseline and report class-level failures |
| Segmentation | Locked Fashionpedia instance masks | Top, bottom, footwear, and headwear masks | IoU and Dice by class | Exceed the simplest threshold/morphology baseline and report class-level failures |
| Recognition | Relevant instances in the locked Fashionpedia test split | Garment/attribute predictions | F1, balanced accuracy, PR-AUC, coverage, majority and HOG-only baselines | Exceed baselines where class support permits and report unsupported classes separately |
| Compliance | Image-level labels derived from the locked Fashionpedia test split | Compliant, non-compliant, or review-required | Macro-F1, decided-case accuracy, coverage, review rate, confusion matrix, and exact reason match | No forced decisions for missing or unsupported evidence; disclose the Fashionpedia-only domain limitation |
