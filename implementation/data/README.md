# Dataset Register

Downloaded data is local and excluded from Git. Keep the original archives and source annotations immutable.

## Candidate comparison

| Candidate | Source URL | Licence | Images/subjects | Labels/annotations | Dress-code relevance | Main limitations | Decision |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| Fashionpedia | [Official project](https://fashionpedia.github.io/home/index.html) | Annotations/ontology: CC BY 4.0; image rights remain with original sources | 48,823 files in the current official archives | 46 apparel categories/parts, 294 attributes, boxes, and instance masks | Collars, sleeves, tops, pants, cargo styles, skorts, distressed garments, necklines, hats, and shoes | Fashion/web domain rather than university scenes; not every policy condition is labelled | **Selected and downloaded** |

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

- **Name:** Fashionpedia.
- **Version:** 2020 official release.
- **Source:** [Fashionpedia project](https://fashionpedia.github.io/home/index.html) and [official CVDF download repository](https://github.com/cvdfoundation/fashionpedia).
- **Citation:** Jia, M., Shi, M., Sirotenko, M., Cui, Y., Cardie, C., Hariharan, B., Adam, H., & Belongie, S. (2020). *Fashionpedia: Ontology, segmentation, and an attribute localization dataset*. European Conference on Computer Vision.
- **Licence:** The annotations and ontology are CC BY 4.0. Fashionpedia does not own the images; use must also follow the terms of each original image source. See the [official terms](https://fashionpedia.github.io/home/data_license.html).
- **Download date:** 2026-07-20.
- **Downloaded contents:** 45,623 training images, 3,200 combined validation/test images, 333,401 training annotations, and 8,781 public validation annotations for 1,158 images.
- **Original labels:** 46 apparel categories and garment parts, 294 localized attributes, bounding boxes, and polygon/RLE instance masks in an extended COCO JSON format.
- **Relevant categories:** `shirt, blouse`, `top, t-shirt, sweatshirt`, `pants`, `shorts`, `skirt`, `dress`, `jumpsuit`, `tights, stockings`, `shoe`, `hat`, `tie`, `hood`, `collar`, `sleeve`, and `neckline`.
- **Relevant attributes:** polo/crop/tank tops, jeans, cargo pants/shorts/skirts, skort, distressed fabric, sleeve lengths, collar types, crew/round/plunging necklines, and off-the-shoulder/one-shoulder styles.
- **Deep-learning restriction:** The dataset is method-neutral, but its published deep-learning baselines must not be used. All detection, segmentation, feature extraction, recognition, and compliance logic in this project must use classical image processing or conventional non-deep-learning machine learning.
- **Known limitations and bias risks:** Images are drawn from fashion, street-style, celebrity, runway, and shopping contexts rather than APU. Labels do not directly encode compliance, tucked-in shirts, all footwear subtypes, excessive piercings, or whether headgear is customary. Class and attribute imbalance, web-image selection bias, cultural variation, and domain shift must be measured and discussed.
- **Planned split:** Derive training and internal validation subsets from the official training split, grouping detected duplicates before splitting. Reserve the 1,158 publicly labelled official validation images as a locked final test set. Use the remaining unlabelled official test images only for qualitative demonstrations unless they are independently annotated.

## Local immutable layout

```text
raw/fashionpedia/
├── archives/
│   ├── train2020.zip
│   └── val_test2020.zip
├── annotations/
│   ├── instances_attributes_train2020.json
│   └── instances_attributes_val2020.json
└── images/
    ├── train/    # 45,623 images
    └── test/     # 3,200 combined validation/test images
```

## SHA-256 integrity record

```text
d896792104a4c35efa7859a18cf605fddae779f5c2372e87e08d7b45949244e2  train2020.zip
44eb1685364b6ed6bda4595fe0dc07a252e9b923112b97b24ff4d440751a2acc  val_test2020.zip
f6af94fb8712bd8170a49c857e842e1227e6806c4f33f32340db0c849133e006  instances_attributes_train2020.json
f831f415edad12d52acde8b138fe7ebd1592b57bf0dcd6a3b63ba8cabd208223  instances_attributes_val2020.json
```

Validation completed after download:

- Both ZIP files passed complete CRC testing with no corrupt member.
- Both annotation files parsed as valid JSON.
- Every image referenced by the training and validation annotations exists locally.
- Every annotation refers to a known image ID.
- A deterministic sample of 100 extracted images passed Pillow decoding.

## Data lifecycle

1. Place untouched source files in `raw/`.
2. Put validated, extracted, or relabelled data in `interim/`.
3. Put model-ready splits and generated annotations in `processed/`.
4. Put genuinely held-out or demonstration images in `test/`.
5. Record every transformation in the corresponding numbered notebook.
