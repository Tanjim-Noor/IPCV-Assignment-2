# Classical University-Attire Pipeline: Diagnostic and Redesign Handover

## Purpose of this document

This document transfers the complete context from the pipeline-review task to a new Codex or ChatGPT conversation.

The project implements a strictly classical computer-vision system for:

1. Detecting university-attire components.
2. Segmenting the detected garments.
3. Recognising dress-code-related properties.
4. Applying deterministic compliance rules.

Deep learning is prohibited throughout the assignment. Any future work must continue using classical image processing and conventional machine learning.

## Requested investigation

The investigation was requested because:

- Full training and evaluation took several hours.
- The full bundle exists under `implementation/models/classical-attire-full/`.
- Inference produced many false clothing detections on background objects.
- Bounding boxes, segmentations, recognition results, and final compliance decisions looked incorrect.
- The user wanted confirmation that the full bundle was used.
- The user wanted clarification about when Fashionpedia labels are converted.
- The user wanted to know whether exact labels or annotations would improve performance.
- The user wanted a comprehensive comparison of improving the current pipeline, changing datasets, changing architecture, or using skin/clothing-presence rules.

No training or full evaluation was rerun during the investigation. The findings came from read-only inspection of:

- Saved manifests and model bundles.
- Executed notebook outputs.
- Saved metrics.
- Pipeline source code.
- Dataset label-conversion code.
- Detection, segmentation, recognition, and compliance implementations.

## Authoritative constraints

Read these before changing the pipeline:

- `AGENTS.md`
- `Assignment Requirements/CT103-3-M-IPCV Assignment - Part 2 (APUMF2604AI).pdf`
- `Assignment Requirements/assignment-2-requirements.md`

The main methodological constraint is:

> Deep learning is strictly prohibited in preprocessing, feature extraction, detection, segmentation, recognition, evaluation, and inference.

Do not introduce:

- Convolutional Neural Networks.
- You Only Look Once detectors.
- U-Net.
- Mask Region-Based Convolutional Neural Networks.
- Segment Anything Model.
- Vision transformers.
- Deep embeddings.
- Hosted deep-learning services.
- Pretrained deep features hidden inside another library.

Permitted approaches include:

- Histogram of Oriented Gradients.
- Scale-Invariant Feature Transform.
- Oriented FAST and Rotated BRIEF.
- Local Binary Pattern.
- Thresholding and morphology.
- Contours, watershed, graph cuts, and GrabCut.
- Clustering.
- Principal Component Analysis.
- Support Vector Machines.
- k-Nearest Neighbours.
- Random Forests.
- Gradient boosting.
- Classical Deformable Part Models.

## Important repository files

### Models and metrics

- `implementation/models/classical-attire-full/manifest.json`
- `implementation/models/classical-attire-full/bundle.joblib`
- `implementation/models/classical-attire-smoke/`
- `implementation/outputs/metrics/locked-test-metrics.json`

### Notebooks

- `implementation/stages/06_training_and_tuning/06_training_and_tuning.ipynb`
- `implementation/stages/07_evaluation_and_error_analysis/07_evaluation_and_error_analysis.ipynb`
- `implementation/stages/08_inference_and_demo/08_inference_and_demo.ipynb`
- `implementation/stages/09_learning_and_visual_audit/09_learning_and_visual_audit.ipynb`

### Core implementation

- `implementation/src/ipcv_attire/training.py`
- `implementation/src/ipcv_attire/detection.py`
- `implementation/src/ipcv_attire/segmentation.py`
- `implementation/src/ipcv_attire/features.py`
- `implementation/src/ipcv_attire/pipeline.py`
- `implementation/src/ipcv_attire/evaluation.py`
- `implementation/src/ipcv_attire/compliance.py`
- `implementation/src/ipcv_attire/rubric.py`

## Current model-profile status

### Stage 06: training

Stage 06 trained the full profile successfully.

The full manifest records:

- Profile: `full`
- Four detector components:
  - `upper_body`
  - `bottom_body`
  - `footwear`
  - `headwear`
- Recognition targets including:
  - `allowed_sleeve`
  - `casual_or_tight_bottom`
  - `casual_round_neck_top`
  - `collared_top`
  - `damaged_bottom`
  - `formal_bottom_candidate`
  - `leisurewear`
  - `revealing_top`

The inspected full bundle had the recorded SHA-256 value:

```text
69e17521316bd46cdb8e85c13f277d436140eb1c296bf4a6ff65bb4139f02230
```

### Stage 07: locked evaluation

Stage 07 loaded and evaluated the full profile on 1,158 images.

It did not use the smoke model.

### Stage 08: inference and demonstration

At the beginning of the diagnostic review, Stage 08 was configured as:

```python
TRAINING_PROFILE = "smoke"
```

Its previously executed output therefore loaded:

```text
implementation/models/classical-attire-smoke
```

The current working-tree version has since been changed and re-executed with:

```python
TRAINING_PROFILE = "full"
```

The current notebook output records the full profile and full-bundle SHA-256. The full-model inference still produces large numbers of implausible detections, so changing from smoke to full did not resolve the underlying failure.

### Stage 09: learning and visual audit

Stage 09 loaded the full profile.

Its output provides the clearest evidence that the full detector itself is failing. This is not only a smoke-model problem.

## Current end-to-end pipeline

The current pipeline is:

```text
Fashionpedia image and annotations
    ↓
Convert detailed garment categories into four coarse component classes
    ↓
Train four Histogram of Oriented Gradients sliding-window detectors
    ↓
Scan the full input image at many locations and scales
    ↓
Apply Non-Maximum Suppression
    ↓
Run GrabCut separately inside every predicted box
    ↓
Extract handcrafted colour, texture, edge, and shape features
    ↓
Run binary garment-property recognisers
    ↓
Aggregate detected components into one or more outfits
    ↓
Apply deterministic dress-code rules
    ↓
Compliant, non-compliant, or review
```

## Models and techniques currently used

### Detection

Each component detector uses:

- Histogram of Oriented Gradients features.
- A linear maximum-margin classifier trained using:

```python
SGDClassifier(loss="hinge")
```

This is effectively a linear Support Vector Machine objective optimised through stochastic gradient descent.

Inference uses:

- An image pyramid.
- Sliding windows.
- A stride based on a proportion of the window size.
- A decision threshold.
- Non-Maximum Suppression.
- A maximum of eight detections for each component class.

With four component classes, the detector can retain up to:

```text
4 components × 8 detections = 32 detections per image
```

### Segmentation

Segmentation uses GrabCut.

GrabCut is not trained from Fashionpedia masks. It estimates foreground and background from the predicted rectangle and image colours.

Therefore, segmentation quality depends heavily on detection quality. A false or loose box gives GrabCut incorrect foreground/background assumptions.

### Recognition

Recognition uses a combined handcrafted feature vector:

- Histogram of Oriented Gradients for local edge orientation and shape.
- Uniform Local Binary Pattern for texture.
- Hue, Saturation, and Value histograms for colour distribution.
- Colour mean, standard deviation, and skewness.
- Edge density.
- Mask area ratio.
- Mask perimeter.
- Mask aspect ratio.
- Mask solidity.

Every binary recognition target uses:

```python
StandardScaler()
SGDClassifier(loss="log_loss", class_weight="balanced")
```

This is a scaled linear logistic classifier trained through stochastic gradient descent.

Low and high decision thresholds are selected on internal validation data to create:

- Negative evidence.
- Positive evidence.
- Uncertain or review evidence.

### Compliance

Compliance is not a trained model.

It is a deterministic rule engine that consumes recognised garment properties and detector-based proxy evidence.

## When annotation-label conversion occurs

There are three different conversions. Label conversion is not confined to the final rule stage.

### Conversion 1: detailed garment category to detector class

This occurs before detection training.

Examples:

```text
shirt/blouse ┐
top          │
sweater      ├──→ upper_body
cardigan     │
jacket       │
dress        ┘

pants  ┐
tights │
shorts ├──→ bottom_body
skirt  ┘

shoe ────────→ footwear
hat ─────────→ headwear
```

The detector is therefore trained on converted coarse component labels rather than the original full Fashionpedia category taxonomy.

### Conversion 2: categories, parts, and attributes to recognition targets

This also occurs before training.

Fashionpedia garment categories, attributes, collars, sleeves, and necklines are converted into targets such as:

- `collared_top`
- `allowed_sleeve`
- `casual_round_neck_top`
- `revealing_top`
- `formal_bottom_candidate`
- `casual_or_tight_bottom`
- `damaged_bottom`
- `leisurewear`

A garment-part annotation is associated with an upper-body parent when it satisfies the configured containment rule.

These derived binary targets train the recognition classifiers.

### Conversion 3: recognition evidence to compliance

This happens last.

The rule engine converts recognised evidence into:

- Compliant.
- Non-compliant.
- Manual review.
- Specific violation reasons.

### Conclusion about conversion

Detailed labels already affect training. The current pipeline deliberately collapses the detailed categories into coarse detection classes and rule-aligned recognition targets.

The problem is not that annotations are ignored entirely. The problems are:

- Excessive category collapsing.
- Important mask information is unused.
- Some target labels are weak proxies.
- Severe class imbalance.
- Weak detector negatives.
- A major difference between clean training crops and noisy inference crops.

## Exact annotation usage: what is used and what is not

### Already used

- Exact ground-truth bounding boxes create positive detector crops.
- Exact categories determine coarse detector labels.
- Exact categories and attributes derive recognition targets.
- Garment parts contribute collar, sleeve, and neckline evidence.

### Not used effectively

- Fashionpedia polygon masks do not train segmentation.
- Exact masks do not isolate garments during recognition training.
- The detector does not learn from instance-mask shape.
- The detector does not retain most original per-category distinctions.
- Recognition is trained using exact ground-truth boxes but is inferred using noisy predicted boxes.
- Recognition training uses a full rectangular mask when no mask is supplied.

## Major train–inference mismatch

Recognition training receives:

```text
Clean ground-truth garment box
    +
Entire rectangular crop treated as foreground
```

Recognition inference receives:

```text
Often incorrect predicted garment box
    +
GrabCut foreground mask
```

The recognition models therefore learn from clean, tightly localised crops but must predict from noisy boxes, partial garments, backgrounds, and inconsistent segmentation masks.

This distribution mismatch can destroy recognition even if the underlying feature classifier has some value on ground-truth crops.

## Full-model diagnostic results

### Stage 09 visual audit

The full-model audit used three images and produced:

| Measurement | Result |
|---|---:|
| Predicted boxes | 95 |
| True positives | 1 |
| False positives | 94 |
| False negatives | 7 |
| Precision | approximately 1.05% |
| Recall | 12.5% |
| Predictions per image | approximately 31.7 |
| Maximum possible per image | 32 |

This means the full detector nearly fills its entire detection allowance on every audited image.

This behaviour is detector saturation, not a minor threshold error.

### Saved locked-test prediction volume

The locked evaluation retained:

```text
36,632 predictions across 1,158 images
```

That is:

```text
approximately 31.6 predictions per image
```

This independently shows that the detector nearly reaches the 32-box cap across the complete evaluation set.

### Recognition metrics

The saved metrics report approximately:

| Metric | Result |
|---|---:|
| Recognition macro F1 | 0.212 |
| Recognition balanced accuracy | 0.501 |
| Recognition Precision–Recall Area Under the Curve | 0.232 |

Selected target results:

- `allowed_sleeve` performs worse than its majority-class baseline.
- `damaged_bottom` F1 is approximately 0.049.
- `leisurewear` F1 is approximately 0.008.
- Footwear and headwear recognition coverage are zero in the recognition evaluator.

The balanced accuracy near 0.50 indicates chance-like binary recognition overall.

### Compliance collapse

The compliance stage classified all 1,158 evaluation images as non-compliant.

Saved results include approximately:

| Metric | Result |
|---|---:|
| Compliance macro F1 | 0.235 |
| Compliance balanced accuracy | 0.333 |
| Exact reason match | 0.000864 |

An exact reason match of 0.000864 is one correct reason set across 1,158 images.

The failure chain is:

```text
Many false boxes
    ↓
Many unreliable recognition scores
    ↓
At least one apparent prohibited property
    ↓
Every image becomes non-compliant
```

## Evaluation coordinate-system defect

There is an important defect in:

```text
implementation/src/ipcv_attire/evaluation.py
```

The evaluation loads:

- Ground-truth boxes in original Fashionpedia image coordinates.
- Predictions in resized/preprocessed image coordinates.

It then performs box matching without consistently applying the preprocessing scale to ground-truth boxes.

For images resized during preprocessing, Intersection over Union is therefore calculated between incompatible coordinate systems.

### Metrics affected

This invalidates or severely distorts:

- Detection true-positive count.
- Detection false-negative count.
- Precision.
- Recall.
- Average Precision at Intersection over Union 0.50.
- Average Precision from 0.50 to 0.95.
- Matched-mask count.
- End-to-end segmentation metrics that depend on matched boxes.
- The centre-window detection baseline when it is matched the same way.

### What the defect does not explain

The defect does not:

- Create false inference boxes.
- Change the detector.
- Change the number of retained predictions.
- Explain the background detections visible in Stage 08.
- Explain the correctly scaled Stage 09 audit.

Stage 09 scales ground truth correctly and still reports 94 false positives out of 95 predictions.

Therefore:

> The locked detection metrics are numerically unreliable, but the model is still visibly and structurally failing.

## Recognition-evaluation concerns

The recognition evaluator also needs redesign.

### Maximum aggregation across all predictions

Image-level target scores are aggregated using a maximum across detected components.

When the detector produces approximately 32 components per image, one high false score can dominate the image-level result.

This creates a multiple-comparison effect:

```text
More false components
    → more opportunities for one extreme score
        → more false dress-code violations
```

### Footwear and headwear coverage

Footwear and headwear proxy evidence is introduced later in the pipeline from detector presence.

The recognition evaluator reads component recognition predictions. Footwear and headwear components do not have equivalent learned recognition outputs, leading to zero recognition coverage even though the compliance rules may still use their proxy presence.

Detection proxy metrics and learned recognition metrics must be reported separately.

## Why the current detector fails

### One model represents too many shapes

The `upper_body` detector includes highly different categories such as:

- Shirts.
- T-shirts.
- Sweaters.
- Cardigans.
- Jackets.
- Vests.
- Coats.
- Dresses.
- Jumpsuits.

A rigid linear Histogram of Oriented Gradients template cannot easily represent this visual diversity.

### Negative sampling is weak and can be incorrectly labelled

For each positive garment crop, training selects one random negative crop.

The negative is mainly checked against the current positive bounding box. It is not robustly excluded from every other clothing annotation in the image.

Consequently, some negative crops may contain:

- Other garments.
- Body parts.
- Clothing texture.
- Parts of the current person.

This introduces label noise.

### Hard-negative mining is not genuine detector mining

The implementation samples another random crop and retains it if the current classifier scores it positively.

True hard-negative mining should:

1. Run the detector over full training images and background images.
2. Collect the highest-scoring false detection windows.
3. Confirm they do not overlap any target annotation.
4. Add them as negatives.
5. Retrain.
6. Repeat for several rounds.

The current implementation does not scan and mine the real false detections that appear during inference.

### The detector searches the entire image

The four component detectors scan:

- People.
- Walls.
- Furniture.
- Trees.
- Bags.
- Text.
- Shadows.
- Skin.
- Background patterns.

There is no person or body-location constraint.

This is the most important architectural cause of the background false positives.

### Fixed windows are too restrictive

The detector uses a small set of fixed aspect ratios.

Clothing changes shape because of:

- Pose.
- Camera angle.
- Occlusion.
- Loose or tight fit.
- Long or short garments.
- Cropped people.
- Sitting or standing subjects.

### Scores are not calibrated probabilities

The detector converts raw linear decision margins with a sigmoid.

These values are displayed as probability-like confidence scores, but they are not properly calibrated probabilities. Many false detections saturate near 1.0.

### Non-Maximum Suppression cannot solve distributed false positives

Non-Maximum Suppression removes overlapping duplicates from the same class.

It does not remove different false detections spread across unrelated parts of an image.

## Training-data imbalance

The inspected full training samples were approximately:

| Component | Samples |
|---|---:|
| `upper_body` | 45,852 |
| `footwear` | 37,458 |
| `bottom_body` | 19,910 |
| `headwear` | 2,087 |

Selected recognition-target counts were approximately:

| Target | Positive samples |
|---|---:|
| `footwear` | 37,458 |
| `allowed_sleeve` | 26,755 |
| `collared_top` | 9,006 |
| `casual_round_neck_top` | 9,004 |
| `revealing_top` | 6,277 |
| `formal_bottom_candidate` | 5,374 |
| `casual_or_tight_bottom` | 5,135 |
| `headwear` | 2,087 |
| `damaged_bottom` | 568 |
| `leisurewear` | 236 |
| `skort` | 5 |

Class weighting cannot manufacture reliable visual patterns from extremely rare labels.

Targets such as `skort`, `leisurewear`, and `damaged_bottom` need one or more of:

- More data.
- Carefully merged categories.
- A rule-based fallback.
- A manual-review state.
- Removal from learned claims when insufficiently supported.

## Would exact annotations improve the system?

### Exact boxes alone

Exact boxes are already used for positive detector crops.

Using them again will not fix full-image sliding-window inference.

### Exact category labels

Keeping more category detail may reduce within-class variation.

However, training all Fashionpedia categories separately would increase:

- Class imbalance.
- Model count.
- Evaluation complexity.
- Confusion between visually similar garments.

A better compromise is a rule-aligned intermediate taxonomy:

- Shirt or top.
- Outerwear.
- Dress or jumpsuit.
- Trousers.
- Shorts or skirt.
- Footwear.
- Headwear.

These can later be merged into the assignment’s required regions.

### Exact polygon masks

Using exact masks is the highest-value annotation improvement.

Fashionpedia masks could train a classical pixel- or superpixel-level model for:

- Clothing.
- Skin.
- Hair.
- Background.
- Uncertain boundary.

Exact masks should also isolate garments during recognition training.

### Exact annotations during evaluation

Ground-truth boxes and masks should be used for oracle experiments.

Oracle input is not deployable inference. It is a diagnostic method that answers:

> How well would segmentation or recognition work if the earlier stage were correct?

## Recommended oracle experiments

Run these before another expensive full training session.

### Experiment A: recognition upper bound

```text
Ground-truth box
    +
Ground-truth mask
    →
Existing recognition model
```

Purpose:

- Measures whether the trained recogniser has useful signal with perfect localisation.
- Separates recognition weakness from detection and segmentation weakness.

### Experiment B: segmentation isolation

```text
Ground-truth box
    +
GrabCut
    →
Segmentation metric
    →
Recognition
```

Purpose:

- Measures GrabCut without detector error.
- Shows whether GrabCut itself is adequate for tight garment boxes.

### Experiment C: current end-to-end pipeline

```text
Predicted box
    +
GrabCut
    →
Recognition
```

Purpose:

- Measures actual deployable performance.

### Interpretation

| Result pattern | Meaning |
|---|---|
| A good, B good, C bad | Detection is the main failure |
| A good, B bad | Segmentation harms recognition |
| A bad | Recognition features, labels, or models are weak |
| A and B good but compliance bad | Aggregation or rules are wrong |

These experiments can use existing trained models. They should not require full retraining.

## Recommended new architecture

The strongest feasible classical redesign is a person-first, body-zone pipeline.

```text
Input image
    ↓
Classical person detector
    ↓
Person Region of Interest
    ↓
Normalised head, torso, legs, and feet zones
    ↓
Coarse clothing segmentation inside the person
    ↓
Zone-specific recognition models
    ↓
Rule evidence with uncertainty
    ↓
Compliant, non-compliant, or review
```

### Step 1: detect the person

Use a classical Histogram of Oriented Gradients plus linear Support Vector Machine person detector.

OpenCV provides a default classical people detector:

```python
cv2.HOGDescriptor_getDefaultPeopleDetector()
```

Before using its pretrained weights:

- Verify that the implementation is classical.
- Document the source.
- Cite the model and training method.
- Confirm lecturer acceptance of pretrained classical models if needed.

A Haar or Local Binary Pattern cascade can provide optional face/head confirmation. It should not be the only person detector.

### Step 2: restrict all garment analysis to the person

Do not scan the whole image for:

- Shoes.
- Hats.
- Upper garments.
- Lower garments.

Only analyse plausible locations inside the detected person.

This should remove most wall, tree, furniture, and background false positives.

### Step 3: use normalised body zones

For approximately upright full-body images, initialise:

- Head/headwear zone: top 15–20%.
- Torso zone: shoulder region to waist.
- Lower-body zone: waist to ankles.
- Footwear zone: bottom 10–20%.

These are priors, not final segmentations.

Contours, foreground masks, colour boundaries, and superpixels can refine them.

### Step 4: train coarse segmentation from masks

Train a non-deep-learning pixel or superpixel classifier.

Candidate models:

- Random Forest.
- Support Vector Machine.
- Gradient Boosting.
- Gaussian Mixture Model plus graph cut.

Candidate features:

- Hue, Saturation, and Value colour.
- CIELAB colour.
- Local Binary Pattern texture.
- Gradient magnitude.
- Edge density.
- Normalised body position.
- Distance from person boundary.
- Superpixel colour mean and variance.
- Superpixel texture.

GrabCut can remain as:

- A baseline.
- A mask refinement step.
- A method initialised by stronger foreground/background seeds.

### Step 5: train zone-specific recognition

Recommended target groups:

#### Torso

- Collar present.
- Round neckline.
- Sleeve length.
- Revealing or open region.

#### Lower body

- Trousers versus shorts or skirt.
- Formal versus casual.
- Damage or rips.
- Tight or leisurewear evidence.

#### Feet

- Footwear present.
- Plausible shoe foreground.

#### Head

- Headwear present.

Candidate classical classifiers:

- Logistic linear classifier as an interpretable baseline.
- Support Vector Machine with a Radial Basis Function kernel.
- Random Forest.
- Gradient Boosting.

Do not assume one model is best for every target. Compare models on internal validation data.

## Alternative architecture options

### Improve the existing detector

Possible improvements:

- Add a person Region of Interest.
- Add several aspect-ratio templates per component.
- Use genuine iterative hard-negative mining.
- Calibrate decision scores.
- Select per-class thresholds from precision–recall curves.
- Limit outputs by body zone.
- Allow only one or two plausible detections per zone.
- Use category-specific models before merging.

Expected benefit: medium.

This is less work than a complete redesign but may remain limited by rigid sliding windows.

### Classical Deformable Part Model

A Deformable Part Model combines:

- A root template.
- Local part templates.
- Geometric constraints between parts.

It can represent variable garment shapes better than one rigid window.

Expected benefit: medium to high.

Cost:

- High implementation complexity.
- High training cost.
- Harder explanation and debugging.

Only pursue this if the simpler person-first body-zone system is insufficient and enough time remains.

### Full-person multi-label classifier

A person crop could be classified directly for:

- Collar evidence.
- Sleeve evidence.
- Formal-bottom evidence.
- Footwear presence.
- Headwear presence.

This may improve final dress-code classification, but it cannot replace the assignment’s detection and segmentation requirements.

Use it only as:

- An auxiliary model.
- A comparison baseline.
- A consistency check against region-level predictions.

## Dataset decision

### Do not replace Fashionpedia immediately

Fashionpedia is not a perfect university-attire dataset, but it contains:

- Garment bounding boxes.
- Polygon masks.
- Garment categories.
- Garment parts.
- Fine-grained attributes.

The current pipeline discards much of this information.

Changing datasets while keeping the same unrestricted sliding-window architecture is unlikely to solve the main failure.

### Recommended hybrid

Retain Fashionpedia for garment attributes and rule-specific labels.

Supplement it with:

- A person-centred human-parsing dataset for coarse segmentation.
- A small, consented university-domain validation/test set.

### ModaNet

Potential value:

- More than 55,000 street-fashion images.
- Polygon garment annotations.
- Simpler 13-class taxonomy.

Limitations:

- Fewer rule-specific attributes.
- Weak support for collar, sleeve, damage, and formality targets.
- Still fashion-oriented.

Use as a segmentation or coarse-category supplement, not a complete replacement.

### Look Into Person

Potential value:

- More than 50,000 person-centred images.
- Semantic person and clothing labels.
- Challenging viewpoints, occlusions, and backgrounds.

Limitations:

- Coarse clothing categories.
- Does not directly annotate the complete university dress-code rubric.

This is a strong candidate for person-centred preprocessing and coarse segmentation.

### Crowd Instance-level Human Parsing

Potential value:

- 38,280 multi-person images.
- Pixel labels and instance identities.

Limitations:

- More complex than needed for a single-person demonstration.
- Coarse labels.

Use it if multi-person analysis is an explicit requirement.

### Small university-domain dataset

A small local dataset would provide the closest match to the intended deployment.

If permitted:

- Collect consented full-body images.
- Include formal, casual, compliant, non-compliant, and ambiguous examples.
- Include ordinary university backgrounds.
- Include variation in lighting, camera distance, body shape, and clothing colour.
- Split by person, not by image.
- Keep faces protected or cropped if identity is unnecessary.
- Document consent, purpose, storage, and deletion.

This dataset should primarily serve validation and final testing. If used for training, use a separate subject-independent test set.

## Skin-detection proposal

Skin detection should not become the central method.

It cannot reliably determine:

- Collar presence.
- Formal trousers.
- Shorts versus skirt in all poses.
- Ripped fabric.
- Leisurewear.
- Shoes.
- Hats.

Skin-colour detection is sensitive to:

- Illumination.
- White balance.
- Camera response.
- Compression.
- Skin-tone diversity.
- Skin-coloured backgrounds.
- Wood, sand, walls, and clothing.

It may also introduce fairness concerns if fixed thresholds behave differently across people.

### Acceptable limited use

Skin evidence may be used:

- Only after a person is detected.
- Only inside plausible torso or arm zones.
- As one low-weight feature.
- To support exposed-area estimation.
- With an uncertain state.
- With evaluation across diverse appearances and lighting.

Never use skin colour alone as an automatic non-compliance rule.

### Assignment concern

A skin-presence plus clothing-presence rubric is likely too simple to demonstrate:

- Clothing detection.
- Clothing segmentation.
- Garment recognition.
- Rule-specific dress-code reasoning.

It should not replace the required pipeline.

## Required evaluation redesign

Detection, segmentation, recognition, and compliance must be evaluated separately.

### Detection evaluation

First scale all ground-truth boxes into the same coordinate system as predictions.

Report:

- Per-class precision.
- Per-class recall.
- Average Precision at Intersection over Union 0.50.
- Average Precision from 0.50 to 0.95.
- False positives per image.
- Precision–recall curves.
- Detection count per image.
- Confusion between component classes when meaningful.

### Segmentation evaluation

Evaluate:

1. Ground-truth box plus segmenter.
2. Predicted box plus segmenter.

Report:

- Mean Intersection over Union.
- Dice coefficient.
- Per-class Intersection over Union.
- Matched-mask count.
- Ground-truth rectangle-mask baseline.

The saved rectangle-mask baseline is approximately 0.534 mean Intersection over Union. A learned or refined segmenter should beat it under ground-truth boxes before being accepted.

### Recognition evaluation

Evaluate three conditions:

1. Ground-truth box plus ground-truth mask.
2. Ground-truth box plus predicted mask.
3. Predicted box plus predicted mask.

For every target, report:

- Precision.
- Recall.
- F1.
- Balanced accuracy.
- Precision–Recall Area Under the Curve.
- Majority-class baseline.
- Positive-class prevalence.
- Decided coverage.
- Manual-review rate.

Do not evaluate recognition only by taking the maximum target score across dozens of unmatched detections.

### Compliance evaluation

Report:

- Macro F1.
- Balanced accuracy.
- Confusion matrix.
- Per-rule precision and recall.
- Manual-review rate.
- Decided coverage.
- Exact violation-reason match.
- Upstream error source for each incorrect decision.

## Recommended implementation sequence

### Phase 0: preserve the current baseline

- Keep the current full bundle as Baseline Version 1.
- Preserve the failed output figures and metrics.
- Document that the baseline demonstrates why unrestricted garment sliding windows fail.
- Do not overwrite it without recording a new model version.

### Phase 1: repair measurement

- Fix ground-truth coordinate scaling in `evaluation.py`.
- Add assertions that predictions and truth use the same image dimensions.
- Separate oracle-box and predicted-box segmentation.
- Separate oracle-crop and end-to-end recognition.
- Report false positives per image.
- Do not rerun full evaluation until the fix is reviewed on a tiny subset.

### Phase 2: perform no-retraining oracle diagnostics

- Use the existing full recognisers.
- Evaluate ground-truth boxes and masks.
- Evaluate ground-truth boxes with GrabCut.
- Compare against predicted boxes.
- Determine whether existing recognition models have any recoverable value.

### Phase 3: build a small person-first pilot

- Detect one principal standing person.
- Restrict garment analysis to that person.
- Apply body-zone priors.
- Test on a small validation subset.
- Measure false positives per image before training a full replacement.

### Phase 4: use exact masks

- Parse Fashionpedia polygons.
- Build clothing/background or coarse-region mask targets.
- Train a small classical pixel or superpixel classifier.
- Compare against GrabCut and rectangle baselines.

### Phase 5: improve recognition

- Train on ground-truth masks.
- Add box-jitter and mask-noise augmentation.
- Compare linear logistic, Support Vector Machine, Random Forest, and Gradient Boosting models.
- Tune thresholds on validation only.
- Keep an uncertain/manual-review range.

### Phase 6: full retraining

Only start another hours-long training run after the small pilot meets acceptance gates.

## Suggested acceptance gates

Before full training:

- Reduce retained detections from approximately 31.6 per image to a small plausible number.
- Target approximately two to four meaningful garment regions per single-person image.
- Make the oracle-box segmenter beat the 0.534 rectangle-mask baseline.
- Require every learned recognition target to beat its majority baseline.
- Remove or convert unsupported rare targets to review/rule-based handling.
- Ensure compliance predicts more than one class on validation data.
- Require false-positive analysis on ordinary backgrounds.
- Confirm that confidence values correspond to empirical precision.

## Option ranking

| Option | Expected improvement | Complexity | Recommendation |
|---|---:|---:|---|
| Use full bundle in Stage 08 | Small | Very low | Already corrected in working tree |
| Increase thresholds only | Small | Low | Diagnostic, not a solution |
| Genuine hard-negative mining | Medium | Medium | Recommended |
| Person-first body-zone pipeline | High | Medium | Primary recommendation |
| Train segmentation from exact masks | High | Medium to high | Primary recommendation |
| More specific garment detectors | Medium | High | Optional |
| Classical Deformable Part Model | Medium to high | Very high | Only if needed |
| Full-person multi-label classifier | Medium | Medium | Auxiliary only |
| Replace Fashionpedia only | Low | High | Not recommended |
| Skin/presence-only rubric | Low and risky | Medium | Not recommended |

## Current workspace caution

At the time this handover was written, the working tree already contained user changes and generated artifacts.

Notable existing state included:

- Modified `.gitignore`.
- Modified and re-executed Stage 08 notebook.
- Untracked raw Fashionpedia data.
- Untracked processed and interim data.
- Untracked model bundles.
- Untracked prediction outputs.

The `.gitignore` rules for datasets, models, and generated predictions had been commented out in the current working tree.

Do not stage or commit:

- Downloaded datasets.
- Raw Fashionpedia images.
- Cached features.
- Model bundles.
- Large prediction outputs.

Restore appropriate ignore behaviour carefully, preserving any intentional user changes. Do not use destructive Git commands.

## Main conclusion for the next task

The current system is not failing because training was too short.

It is failing because:

1. Four coarse detectors represent excessive visual variation.
2. The detectors scan every part of the image without a person constraint.
3. Negative sampling is weak and can contain clothing.
4. Hard-negative mining does not mine actual inference failures.
5. Detector confidence is not properly calibrated.
6. The detector nearly reaches its 32-box cap on every image.
7. Segmentation depends on incorrect boxes.
8. Recognition is trained on clean boxes but inferred on noisy boxes and masks.
9. Rare recognition labels are severely underrepresented.
10. Maximum aggregation lets one false component create an image-level violation.
11. Compliance consequently collapses to non-compliant.
12. The locked detection/segmentation evaluation contains a coordinate-scaling defect.

The recommended direction is:

> Preserve the existing system as a failed baseline, repair evaluation, run oracle diagnostics with the existing bundle, and redesign around classical person detection, body zones, exact-mask segmentation, and zone-specific recognition.

Do not spend several more hours retraining the unchanged architecture.

## Suggested opening prompt for a new conversation

```text
Read AGENTS.md, Assignment Requirements/assignment-2-requirements.md, and
PIPELINE_DIAGNOSTIC_HANDOVER.md completely.

Inspect the current repository state and verify the handover against live files.
Do not run full training or full evaluation.

First:
1. Confirm the evaluation coordinate-scaling defect.
2. Design oracle-box and oracle-mask diagnostics using the existing full bundle.
3. Propose a concrete implementation plan for a classical person-first,
   body-zone pipeline that continues to satisfy the strict no-deep-learning rule.
4. Preserve the existing full model and outputs as Baseline Version 1.
5. Do not modify files until the proposed scope and affected files are clear.
```

## External method and dataset references

- Fashionpedia: <https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123460307.pdf>
- Histogram of Oriented Gradients person detection: <https://www.cs.princeton.edu/courses/archive/fall13/cos429/papers/Dalal05.pdf>
- OpenCV classical people detector example: <https://docs.opencv.org/master/df/d54/samples_2cpp_2peopledetect_8cpp-example.html>
- OpenCV cascade classifier documentation: <https://docs.opencv.org/master/db/d28/tutorial_cascade_classifier.html>
- GrabCut: <https://www.microsoft.com/en-us/research/wp-content/uploads/2004/08/siggraph04-grabcut.pdf>
- ModaNet: <https://arxiv.org/abs/1807.01394>
- Look Into Person: <https://openaccess.thecvf.com/content_cvpr_2017/papers/Gong_Look_Into_Person_CVPR_2017_paper.pdf>
- Crowd Instance-level Human Parsing: <https://openaccess.thecvf.com/content_ECCV_2018/papers/Ke_Gong_Instance-level_Human_Parsing_ECCV_2018_paper.pdf>
- Classical Deformable Part Models: <https://cs.brown.edu/people/pfelzens/papers/cacm.pdf>
