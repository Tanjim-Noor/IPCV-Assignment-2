# University Attire External Test Protocol

## Purpose and scope

Create a locked external-domain test set that measures whether the Fashionpedia-trained classical pipeline transfers to university-like environments. The set supplements, rather than replaces, the larger Fashionpedia evaluation.

## Participants and consent

- Recruit 8-12 consenting adults; do not photograph minors or bystanders.
- Obtain written consent covering image processing, deidentification, coursework storage, lecturer access, and submission.
- Store signed consent forms and original identifiable photographs outside Git. Use anonymous participant and consent IDs in the dataset.
- Credit anyone who contributes materially to capture or annotation in the report.

## Capture specification

- Capture 100 single-person, full-body RGB images at a minimum of 1280 x 720 pixels.
- Keep the full head, top, bottom wear, and both feet visible unless an image is intentionally collected as an occlusion/review-required case.
- Target approximately 50 compliant and 50 university-safe non-compliant outfits.
- Vary classroom, library-like, and common-area backgrounds where photography is permitted; vary lighting, distance, pose, sleeve length, garment colour, and viewpoint.
- Represent non-compliance with round-neck T-shirts, cargo/sweat/track pants, ripped jeans, caps, slippers/flip-flops, or other non-revealing examples. Do not ask participants to wear revealing attire.
- Avoid multiple simultaneous policy violations in at least half of the non-compliant images so individual rule performance remains measurable.

## Privacy processing

1. Copy each original to a private working location and assign `participant_id` and `outfit_id`.
2. Strip all EXIF and location metadata.
3. Detect faces with a documented classical Haar cascade and apply Gaussian blur.
4. Manually inspect every image and correct missed or incomplete face blurring without using an AI segmentation tool.
5. Store only the deidentified copy under `implementation/data/test/university_attire/`.

## Ground-truth schema

Record one row per image with:

- `image_id`, `participant_id`, `outfit_id`, and anonymized `consent_id`;
- `deidentified` and `consent_verified` booleans;
- visible-region flags for head, upper body, lower body, and footwear;
- per-rule status: `pass`, `fail`, `unknown`, or `not_applicable`;
- final decision: `compliant`, `non_compliant`, or `review_required`;
- person, top, bottom, footwear, and headwear bounding boxes; and
- notes for occlusion, ambiguity, or capture defects.

Manually draw top, bottom, footwear, and headwear polygons for a balanced 30-image subset. Use an offline manual polygon tool with automatic or AI-assisted segmentation disabled.

## Quality control and locking

- Label every image twice in separate passes and reconcile inconsistencies before locking the set.
- Verify that no participant name, face, EXIF location, or consent document appears in the repository copy.
- Hash the final images and annotation file. Record the hashes and lock date in the local data card.
- Do not inspect model predictions on this set until training, feature selection, thresholds, and hyperparameters are frozen.
