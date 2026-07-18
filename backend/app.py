import io
import os
import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from document import load_document, save_document, redact_document

app = FastAPI(title="PII Redaction Tool API")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

# If allow_credentials is True, Starlette/FastAPI raises a RuntimeError if "*" is in allow_origins.
if "*" in allowed_origins:
    allowed_origins = [o for o in allowed_origins if o != "*"]
    if not allowed_origins:
        allowed_origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/")
async def health_check():
    return {"status": "ok", "service": "pii-redaction-tool-api"}

@app.on_event("startup")
def startup_event():
    print("Loading models...")
    import time
    t0 = time.time()
    from detector import initialize_detector
    initialize_detector()
    t_load = time.time() - t0
    print(f"Models loaded in {t_load:.2f}s")

@app.post("/redact")
async def redact_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported.")

    import time
    t_start = time.time()

    try:
        print("Reading document...")
        t_read_start = time.time()
        file_bytes = await file.read()
        doc = load_document(io.BytesIO(file_bytes))
        t_read_end = time.time()
        t_read_docx = t_read_end - t_read_start

        paragraph_texts = []
        for paragraph in doc.paragraphs:
            stripped = paragraph.text.strip()
            if stripped:
                paragraph_texts.append(paragraph.text)

        table_texts = []
        for table in doc.tables:
            for cell in table._cells:
                for paragraph in cell.paragraphs:
                    stripped = paragraph.text.strip()
                    if stripped:
                        table_texts.append(paragraph.text)

        unique_paragraphs = []
        seen_p = set()
        for text in paragraph_texts:
            if text not in seen_p:
                seen_p.add(text)
                unique_paragraphs.append(text)

        unique_tables = []
        seen_t = set()
        for text in table_texts:
            if text not in seen_t:
                seen_t.add(text)
                unique_tables.append(text)

        print(f"Scanning PII: Starting detection on {len(unique_paragraphs)} unique paragraphs...")
        t_p_start = time.time()
        from detector import scan_and_build_mapping
        mapping, counts = scan_and_build_mapping(unique_paragraphs, mapping={}, counts={})
        t_p_end = time.time()
        t_p_detect = t_p_end - t_p_start

        print(f"Scanning PII: Starting detection on {len(unique_tables)} unique table cells...")
        t_t_start = time.time()
        mapping, counts = scan_and_build_mapping(unique_tables, mapping=mapping, counts=counts)
        t_t_end = time.time()
        t_t_detect = t_t_end - t_t_start

        print("Redacting document...")
        t_redact_start = time.time()
        redact_document(doc, mapping)
        t_redact_end = time.time()
        t_redact = t_redact_end - t_redact_start

        print("Saving document...")
        t_save_start = time.time()
        out_stream = io.BytesIO()
        save_document(doc, out_stream)
        out_stream.seek(0)
        t_save_end = time.time()
        t_save_docx = t_save_end - t_save_start

        total_time = time.time() - t_start
        print(f"Finished in {total_time:.2f}s")
        print("--- Performance breakdown ---")
        print(f"Reading DOCX:         {t_read_docx:.4f}s")
        print(f"Paragraph detection:  {t_p_detect:.4f}s")
        print(f"Table detection:      {t_t_detect:.4f}s")
        print(f"Replacement:          {t_redact:.4f}s")
        print(f"Saving DOCX:          {t_save_docx:.4f}s")
        print(f"Total time elapsed:   {total_time:.4f}s")
        print("-----------------------------")

        headers = {
            "Content-Disposition": f"attachment; filename=redacted_{file.filename}",
            "Access-Control-Expose-Headers": "X-Detected-PII",
            "X-Detected-PII": json.dumps(counts)
        }

        out_stream.seek(0)
        return StreamingResponse(
            out_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to redact document: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
