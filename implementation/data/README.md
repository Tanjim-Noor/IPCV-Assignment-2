# Dataset Register

Downloaded data is local and excluded from Git. Keep the original archives and source annotations immutable.

## Candidate comparison

| Candidate | Source URL | Licence | Images/subjects | Labels/annotations | Dress-code relevance | Main limitations | Decision |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| Fashionpedia | [Official project](https://fashionpedia.github.io/home/index.html) | Annotations/ontology: CC BY 4.0; image rights remain with original sources | 48,823 local images | 46 apparel categories/parts, 294 attributes, boxes, and instance masks | Strongest available mapping to collars, sleeves, tops, pants, casual bottoms, distressed garments, necklines, hats, and shoes | Fashion/web domain; sensitive presentation content; several policy conditions are missing | **Primary source retained** |
| ModaNet | [Official repository](https://github.com/eBay/modanet) | Annotation data: CC BY-NC 4.0 | 55,176 street-fashion images | Polygon masks for 13 meta-categories | Detection and segmentation | Same fashion-domain concern, fewer compliance attributes | Rejected as a replacement |
| LIP | [Official resource page](https://www.sysu-hcp.net/resources/datasets/index.html) | Non-commercial research/teaching terms | More than 50,000 person images | 19 coarse human-part labels | General human parsing | Insufficient collar, neckline, cargo, and distressed-style detail | Rejected as a replacement |
| SYSU-Clothes/CCP | [Official dataset page](https://cse.sysu.edu.cn/hcp/article/146) | Verify terms before use | 2,098 street-fashion images | 59 tags; 1,000+ pixel-labelled images | Small clothing-parsing benchmark | Smaller and still fashion-oriented | Rejected as a replacement |
| Open Images V7 | [Official description](https://storage.googleapis.com/openimages/web/factsfigures_v7.html) | Annotations: CC BY 4.0; image licences require verification | Approximately 9 million images | Broad boxes and masks | Potential contextual diversity | Training masks used neural-network-assisted annotation; excluded under the strict method rule | Rejected |

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

## Final use policy

Fashionpedia is the only dataset used by the system. The complete metadata is audited, but feature extraction and training use only garment instances that contribute to a supported dress-code target. Sensitive examples remain available for learning inappropriate-attire classes, while every image displayed in a report, notebook, demonstration, or submission must be automatically risk-filtered and explicitly approved in `showcase-manifest.csv`.

The tracked `dataset-policy.json` is the source of truth for:

- relevant garment categories and attributes;
- derived recognition targets;
- the university-safe display-risk filter;
- minimum class-support thresholds;
- deterministic split seed and ratio; and
- valid showcase-review statuses.

The generated local manifests are:

```text
interim/manifests/
├── fashionpedia-images.csv
├── fashionpedia-annotations.csv
├── manifest-summary.json
└── showcase-candidates.csv
```

The split builder groups records by normalized original source URL, stratifies by the multi-label target signature, assigns 80% to training and 20% to internal validation, and leaves the official labelled validation split locked. A later perceptual-hash audit must merge any visually duplicated groups before final model training.

### Supported and review-required conditions

Composite models may be trained for collared tops, allowed sleeve lengths, round-neck casual tops, revealing tops, formal-bottom candidates, casual/tight bottoms, damaged bottoms, skorts, leisurewear, footwear presence, and headwear presence. A standalone target is supported only when it has at least 100 positive training images and 20 positive locked-validation images.

The operational rule set is stored in `dataset-policy.json`. A prohibited target takes precedence and produces `NON_COMPLIANT`. An image is `COMPLIANT` only when a collared top, allowed sleeve, formal-bottom candidate, and footwear are all evidenced and no prohibited target is present. Incomplete or uncertain evidence produces `REVIEW_REQUIRED`.

Fashionpedia cannot reliably establish tucked-in status, excessive piercings, exact open-toe footwear subtype, or whether headgear is customary. Formal bottoms are proxied as pants without jeans or casual-bottom attributes, footwear is limited to presence, and a Fashionpedia hat is treated as prohibited headwear. These limitations must be reported rather than guessed from gender, culture, or appearance.

## Presentation safety

- Metadata automatically rejects high-risk crop, halter, camisole, tank, tube, plunging, off-shoulder, micro/mini, swim/leisure, cut-out, and similar attributes from the candidate display pool.
- Metadata is not sufficient for content review. Every displayed Fashionpedia image requires a manual `approved` row in `showcase-manifest.csv`.
- Rendering code must call `require_showcase_approval` before loading a Fashionpedia image.
- Rejected statuses record content, quality, domain, rights, or ambiguous-age concerns without deleting the immutable source image.
- Aggregate metrics may use the full relevant test set, but automatic error visualisation may only use approved images.

## Fashionpedia-only evaluation

- Split the official training annotations by duplicate group into model training and internal validation partitions.
- Reserve the official labelled validation split as the locked final quantitative test.
- Use official unlabelled test images only for qualitative demonstrations after the same showcase approval gate.
- Do not claim university-domain validation or collect additional photographs. The fashion-to-university domain gap is a documented limitation.

## Manifest audit result

The full builder was executed against the local 2020 release on 22 July 2026:

- 48,823 image files were indexed with no missing references.
- 342,172 valid annotations were retained; 10 zero-area source annotations were recorded and excluded.
- 42,125 images contribute to at least one derived recognition target.
- 22,267 images were automatically flagged as unsuitable for showcase candidacy.
- The grouped deterministic split contains 36,889 training, 8,734 internal-validation, 1,158 locked labelled-test, and 2,042 unlabelled qualitative-only images; no duplicate group crosses training and internal validation.
- The image-level operational rules yield 1,665 compliant, 21,011 non-compliant, and 24,105 review-required labelled images.
- Ten of the eleven derived targets pass the standalone support gate. Skort has only five positive training images and no internal-validation or locked-test positives, so it remains a rule target but cannot support a standalone learned classifier.
- Two hundred non-risk-flagged images were shortlisted for manual review. Forty non-revealing examples passed contact-sheet review and are explicitly approved in `showcase-manifest.csv`; every other Fashionpedia image remains blocked from presentation.

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
- Ten training annotations have zero-area boxes. Their links are valid, the raw JSON remains unchanged, and the manifest builder records and excludes them from model-ready data.

## Data lifecycle

1. Place untouched source files in `raw/`.
2. Put validated, extracted, or relabelled data in `interim/`.
3. Put model-ready splits and generated annotations in `processed/`.
4. Put genuinely held-out or demonstration images in `test/`.
5. Record every transformation in the corresponding numbered notebook.
