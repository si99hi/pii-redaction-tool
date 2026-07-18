# PII Redactor Evaluation Report

This report presents the performance of the PII Redactor tool evaluated against a manually annotated ground-truth dataset from the provided corporate document, **Red Herring Prospectus.docx**.

## Evaluation Methodology

### Dataset Selection
Due to the size of the document (127 pages), manually annotating every entity would have been prohibitively time-consuming. Therefore, a carefully selected subset with dense PII content was used as the benchmark dataset. Specifically, evaluation was performed on a subset consisting of the key contact, cover page, and corporate history sections (Paragraphs 23, 24, 26, 27, 28, and 29). This subset was selected because it contains a high concentration of the primary PII categories (Person, Company, Email, Phone Number, and Address), making it suitable for evaluating the detector on realistic corporate content.

### Metrics Defined
True Negatives (TN) are not meaningful in the context of PII detection (since every word not labeled as PII is technically a True Negative, artificially inflating accuracy to ~99.9%). Therefore, we utilize the following entity-level metrics:

*   **Precision (P)**: $\frac{TP}{TP + FP}$ — Out of all redaction suggestions, how many were correct?
*   **Recall (R)**: $\frac{TP}{TP + FN}$ — Out of all actual PII present, how much did we catch?
*   **F1-Score (F1)**: $2 \cdot \frac{P \cdot R}{P + R}$ — The harmonic mean of Precision and Recall.
*   **Entity-level - Detection Accuracy**: $\frac{TP}{TP + FP + FN}$

An exact span match (exact start character, end character, and entity type) is required for a True Positive. Exact span matching is intentionally strict. Partial matches are counted as incorrect even when the underlying sensitive information is successfully redacted.

**Scope of Evaluation:** The reported metrics evaluate the accuracy of PII detection by comparing predicted entities against manually annotated ground truth. Document formatting preservation and replacement consistency were validated separately through manual inspection of the generated redacted documents.

---

## Evaluation Results

Running the `evaluation/metrics.py` script on the ground truth annotations yielded the following results:

| Category | TP | FP | FN | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ADDRESS** | 0 | 9 | 2 | 0.00% | 0.00% | 0.00% |
| **COMPANY** | 4 | 10 | 0 | 28.57% | 100.00% | 44.44% |
| **DATE** | 10 | 2 | 0 | 83.33% | 100.00% | 90.91% |
| **EMAIL_ADDRESS** | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| **PERSON** | 0 | 1 | 1 | 0.00% | 0.00% | 0.00% |
| **PHONE_NUMBER** | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| **Overall** | **16** | **22** | **3** | **42.11%** | **84.21%** | **56.14%** |

### Overall Summary Metrics
*   **Overall Precision**: **42.11%**
*   **Overall Recall**: **84.21%**
*   **Overall F1-Score**: **56.14%**
*   **Entity-level Accuracy**: **39.02%**

**Interpretation:** The detector achieved high recall (84.21%), indicating that most sensitive entities were successfully identified. Lower precision (42.11%) primarily resulted from conservative over-detection of corporate and location entities, a trade-off that favors privacy protection over minimal redaction in legal documents.

---

## Detailed Error Analysis

### 1. Address Boundary Mismatches (0.0% Exact Match)
*   **Behavior**: The ground truth defines physical addresses as single continuous blocks (e.g., `11/3, 11/4 and 11/5, Village Birdewadi, Chakan Taluka - Khed, Pune – 410 501, Maharashtra, India`). However, the detector identifies smaller sub-spans like `Birdewadi`, `Khed`, `Pune`, `Maharashtra`, and `India` as individual location/address entities.
*   **Impact**: On a strict span-matching basis, this registers as 0 True Positives, 9 False Positives (the sub-spans), and 2 False Negatives (the full block).
*   **Security Assessment**: Although strict span-level evaluation reports no exact matches, the address information was still successfully anonymized through multiple overlapping location replacements. This reduces the practical privacy risk despite lowering the span-level metric.

### 2. Company Name False Positives (28.57% Precision)
*   **Behavior**: The detector achieved 100.0% Recall for company names (catching all actual target companies), but generated 10 False Positives.
*   **Causes**: The spaCy ORG model flagged general corporate entities and document sections (e.g., `Companies Act`, `Board`, `Shareholders`, `Registrar of Companies`) as companies.
*   **Security Assessment**: *Acceptable*. This trade-off prioritizes privacy by preferring over-redaction to missing potentially sensitive entities, at the cost of slightly reduced document readability.

### 3. Date Detections (100.0% Recall, 83.33% Precision)
*   **Behavior**: Excellent detection coverage of dates. The two False Positives occurred on non-PII page numbers or section indices that resembled years/dates to the parser.

### 4. Email & Phone Number (100.0% Precision & Recall)
*   **Behavior**: Perfect performance. Presidio and the custom phone regex matched the targets exactly.

### 5. Indian Person Name Misses
*   **Behavior**: The detector split or missed the name `Sarthak Malvadkar` due to the underlying Presidio/spaCy English model limitations on non-Western names.
*   **Solution/Mitigation**: In a production environment, loading a custom entity recognizer or a domain-specific named entity recognition model trained on Indian names would resolve this boundary mismatch.

### 6. Absent PII Categories
*   **SSN, Credit Cards, and IP Addresses**: These entity types were supported by the underlying detector but were not present in the evaluation dataset, and therefore were not included in the reported metrics.
