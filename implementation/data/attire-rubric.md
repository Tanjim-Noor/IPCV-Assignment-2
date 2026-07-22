# Operational University Attire Rubric

This rubric converts Fashionpedia-supported evidence into an auditable outcome. It is gender-neutral and entirely classical. A hard failure fixes the outcome as inappropriate, but the pipeline continues evaluating every rule so the report contains all reasons.

| Rule | Evidence and treatment |
| --- | --- |
| Revealing top | Crop, halter, camisole, tank, tube, plunging, sleeveless, off-shoulder, or one-shoulder evidence is an immediate failure. |
| Round-neck casual top | Confident crew- or round-neck casual-top evidence is an immediate failure. |
| Casual/tight bottom | Sweatpants, leggings, cargo pants, track pants, or tights evidence is an immediate failure. |
| Damaged bottom | Distressed or frayed bottom evidence is an immediate failure. |
| Leisurewear | Trunks, boardshorts, lounge shorts, or nightgown evidence is an immediate failure. |
| Headwear | A hat detection is an immediate proxy failure; Fashionpedia cannot encode customary exceptions. |
| Skort | Exact skort evidence would fail, but five positive training images and no validation positives are insufficient for a learned classifier. The inference rule is unsupported and must not be guessed. |
| Collared top | A confident collar passes. A confident negative on a visible upper garment fails. Missing or uncertain evidence requires review. |
| Sleeve length | Short, elbow, three-quarter, or wrist-length evidence passes. A confident negative on a visible top fails. Missing or uncertain evidence requires review. |
| Formal bottom | Pants without jeans or casual-bottom evidence pass as a proxy. Prohibited bottom evidence fails. Otherwise the result requires review. |
| Footwear | A shoe detection passes the presence proxy. Missing or occluded footwear requires review; open-toe subtype is unsupported. |

The following conditions are always reported as unsupported and do not silently change the operational result: tucked-in status, excessive body piercings, exact open-toe footwear subtype, and customary-headgear exceptions.

## Decision precedence

1. Any confident supported failure makes the outfit inappropriate.
2. Otherwise, any unknown required or prohibited rule makes the outfit review-required.
3. Only a complete set of supported passes makes the outfit appropriate.
4. For multiple outfits, any inappropriate outfit makes the image inappropriate; otherwise any review-required outfit makes the image review-required.
5. No detections, ambiguous grouping, invalid input, or inadequate segmentation requires review.

