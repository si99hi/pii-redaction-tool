# PII Redactor

> [!NOTE]
> **Evaluation Metrics**: Evaluation metrics, annotated datasets, and validation reports are present in the [evaluation](./evaluation) folder. You can calculate them directly by running `python evaluation/metrics.py`.

Link:  https://pii-redaction-tool-mu.vercel.app/


A minimal, clean, and professional end-to-end PII Redaction Tool. It allows users to upload a Microsoft Word (`.docx`) prospectus, detects 9 categories of PII using Presidio Analyzer, spaCy, and custom regex fallbacks, replaces detected PII with realistic, format-preserving fake values consistently across the entire document, and returns the redacted file.

The application features a modern, clean, sharp-edged UI (Claude-inspired typography) and standard, exact-match evaluation metrics.

## Screenshots

### Home Screen
![Redaction Result](images/Screenshot%202026-07-18%20032130.png)

### Redaction Result
![Home Screen](images/Screenshot%202026-07-18%20023601.png)

---

## Supported PII Categories

1.  **Person Names** (Presidio + spaCy)
2.  **Email Addresses** (Presidio)
3.  **Phone Numbers** (Presidio + Indian format `+91` preservation regex)
4.  **Company Names** (spaCy ORG + suffix-matching regexes)
5.  **Physical Addresses** (Presidio LOCATION + street suffix-matching regexes)
6.  **Social Security Numbers (SSN)** (Presidio US_SSN + format-matching regex)
7.  **Credit Cards** (Presidio + 13-19 digit card matching regex)
8.  **Dates of Birth** (Presidio DATE_TIME + common date formats with layout-preserving fake dates)
9.  **IP Addresses** (Presidio + IPv4 pattern regex)

---

## Project Structure

```text
scaler file2/
├── backend/
│   ├── app.py                # FastAPI Application and Upload Endpoint
│   ├── document.py           # DOCX Reading, Redacting, and Fallback Styling Logic
│   ├── detector.py           # PII Scanner, Mapping Builder, and Fake Generators
│   └── requirements.txt      # Python Dependencies
├── frontend/
│   ├── src/
│   │   ├── main.jsx          # React Mounting Entrypoint
│   │   └── App.jsx           # Main React component & Vanilla CSS Styling
│   ├── index.html            # Vite entrypoint with Claude-style typography
│   └── package.json          # React Node Dependencies
├── evaluation/
│   ├── ground_truth.json     # Manually annotated prospectus PII dataset
│   ├── metrics.py            # Evaluation metrics calculator (Precision, Recall, F1, Accuracy)
│   └── evaluation_report.md  # Detailed NLP error analysis and metrics write-up
└── README.md                 # This documentation
```

---

## Setup & Running Instructions

### Prerequisite
*   Python 3.8+ (tested on Python 3.13)
*   Node.js 18+ and npm

### 1. Run the Backend Server
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server via Uvicorn
python -m uvicorn app:app --reload --port 8000
```
The server will start running on `http://localhost:8000`.

### 2. Run the Frontend App
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```
The application will be accessible at the URL printed in your console (usually `http://localhost:5173`).

### 3. Run the Evaluation Script
```bash
# Run the evaluation script from the project root
python evaluation/metrics.py
```

---

## Key Design Assumptions & Limitations

### 1. Formatting Preservation vs. Leak Prevention
*   **Assumption**: In `.docx` XML, a single word can be split across multiple formatting "runs" (e.g., `Ra` `hu` `l` if parts are bolded or edited separately). 
*   **Limitation**: Replacing text purely run-by-run will fail if a PII word spans multiple runs.
*   **Handling**: The tool first attempts run-level replacement (preserving styles). If any PII remains, it falls back to paragraph-level replacement, which resets the style of that paragraph to guarantee data privacy. Confident confidentiality takes priority over style preservation.

### 2. Address Boundary Mismatch
*   **Limitation**: Strict NLP metrics show low span-matching scores for addresses. This is because the ground truth labels the entire block as a single address, whereas the detector identifies sub-regions (e.g., specific cities or states) separately. 
*   **Mitigation**: While strict metrics penalize this, all sensitive address components are successfully redacted in practice, maintaining complete privacy.

### 3. Indian Person Names
*   **Limitation**: Out-of-the-box Presidio and spaCy models are trained primarily on Western corpora, occasionally missing or splitting Indian names.
*   **Mitigation**: Custom regexes and fallback filters help mitigate standard name misses.
