# PII Redactor

An end-to-end PII Redaction Tool designed to process Microsoft Word (`.docx`) prospectuses. It detects 9 categories of PII using Presidio Analyzer, spaCy, and custom regex fallbacks, replacing them consistently with realistic synthetic values while preserving document formatting wherever practical.

*   **Live App**: [pii-redaction-tool-mu.vercel.app](https://pii-redaction-tool-mu.vercel.app/)
*   **Architecture Details**: See [architecture.md](./architecture.md) for full pipeline specs and heuristics.
*   **Evaluation Metrics**: Ground truth annotations and calculation scripts are in the [evaluation](./evaluation) folder. Run `python evaluation/metrics.py` to calculate metrics.

---

## Key Features

*   **Consistent Replacement**: Replaces identical PII entities with the same synthetic value throughout the document.
*   **Formatting Preservation**: Attempts formatting-aware (run-level) replacement in Word files, falling back to paragraph-level replacement only when a sensitive span crosses formatting boundaries.
*   **Resource Optimized**: Configured to run on minimal resource constraints (such as Render's 512MB free tier) using spaCy's lightweight `en_core_web_sm` model.
*   **Precision Heuristics**: Employs domain-specific legal whitelists (e.g. *Companies Act*, *SEBI*) to reduce false positives, and contextual DOB filtering to avoid redacting generic dates.

---

## Supported PII Categories

1.  **Person Names** (Presidio + spaCy NER)
2.  **Email Addresses** (Presidio)
3.  **Phone Numbers** (Presidio + Indian `+91` format preservation regex)
4.  **Company Names** (spaCy ORG + suffix-matching regexes)
5.  **Physical Addresses** (Presidio LOCATION + street suffix-matching regexes)
6.  **Social Security Numbers (SSN)** (Presidio US_SSN + format regex)
7.  **Credit Cards** (Presidio + 13-19 digit card regex)
8.  **Dates of Birth** (Presidio DATE_TIME + DOB contextual heuristic filter)
9.  **IP Addresses** (Presidio + IPv4 regex)

---

## Project Structure

```text
├── backend/
│   ├── app.py                # FastAPI endpoints, CORS setup, and performance logging
│   ├── document.py           # DOCX text extraction and run-level substitution
│   ├── detector.py           # PII detection engine, whitelists, and fake generators
│   └── requirements.txt      # Python dependencies (Presidio, spaCy, Faker, etc.)
├── frontend/
│   ├── src/
│   │   ├── main.jsx          # React app entry point
│   │   └── App.jsx           # UI logic, state management, and CSS styles
│   ├── index.html            # HTML template with typography setup
│   └── package.json          # Node dependencies (React, Vite, etc.)
├── evaluation/
│   ├── ground_truth.json     # Hand-annotated prospectus PII dataset (Paragraphs 23, 24, 26-29)
│   ├── metrics.py            # Precision, Recall, F1-score, and entity-level accuracy evaluator
│   └── evaluation_report.md  # Detailed NLP pipeline metrics and error analysis
├── architecture.md           # Visual and technical pipeline documentation
└── README.md                 # This overview
```

---

## Screenshots

### Home Screen
![Home Screen](images/Screenshot%202026-07-18%20023601.png)

### Redaction Result
![Redaction Result](images/Screenshot%202026-07-18%20032130.png)

---

## Setup & Running Instructions

### Prerequisites
*   Python 3.8+ (tested on Python 3.11/3.13)
*   Node.js 18+ and npm

### 1. Run the Backend Server
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Download required spaCy model
python -m spacy download en_core_web_sm

# Run the FastAPI server via Uvicorn
python -m uvicorn app:app --reload --port 8000
```
The API will be available at `http://localhost:8000`.

### 2. Run the Frontend App
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```
The application will run locally at `http://localhost:5173`.

### 3. Run the Evaluation Script
```bash
# Run the evaluation script from the project root
python evaluation/metrics.py
```

---

## Core Limitations & Mitigations

*   **Formatting Boundary Spans**: 
    *   *Issue*: Words split across different XML runs due to mid-word formatting edits can fail run-level replacement.
    *   *Mitigation*: The pipeline falls back to paragraph-level replacement for any un-redacted targets, prioritizing privacy over style where necessary.
*   **Address Span Strictness**: 
    *   *Issue*: Exact-span metrics return low scores because ground-truth annotations label whole multi-line addresses as single blocks, while NLP engines flag individual components (cities, states).
    *   *Mitigation*: Overlapping replacements ensure all sensitive elements are successfully redacted in practice.
*   **Non-Western Name Coverage**: 
    *   *Issue*: Pre-trained English spaCy/Presidio models have reduced accuracy on non-Western names.
    *   *Mitigation*: Custom heuristics, title-prefix lookbehinds, and capitalized-phrase triggers capture missed instances.
