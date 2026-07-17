import string
from docx import Document

def load_document(file_path_or_stream):
    """
    Loads a DOCX document from a file path or file-like binary stream.
    """
    return Document(file_path_or_stream)

def save_document(doc, file_path_or_stream):
    """
    Saves the DOCX document to a file path or file-like binary stream.
    """
    doc.save(file_path_or_stream)

def redact_paragraph(paragraph, mapping_dict):
    """
    Redacts text within a paragraph. 
    First tries run-level replacement to preserve run formatting (bold, italic, etc.).
    Falls back to paragraph-level replacement if the PII text is split across runs.
    """
    text = paragraph.text
    if not text:
        return

    stripped = text.strip()
    if not stripped:
        return

    if len(stripped) <= 2:
        return
    if stripped.isdigit():
        return
    if all(c in string.punctuation or c.isspace() for c in stripped):
        return
    
    lower_text = stripped.lower()
    if lower_text.startswith("page ") and lower_text[5:].strip().isdigit():
        return

    for run in paragraph.runs:
        if not run.text:
            continue
        run_stripped = run.text.strip()
        if not run_stripped or len(run_stripped) <= 2 or run_stripped.isdigit():
            continue
        for original, replacement in mapping_dict.items():
            if original in run.text:
                run.text = run.text.replace(original, replacement)

    full_text = paragraph.text
    needs_fallback = False
    for original in mapping_dict.keys():
        if original in full_text:
            needs_fallback = True
            break

    if needs_fallback:
        new_text = full_text
        for original, replacement in mapping_dict.items():
            new_text = new_text.replace(original, replacement)
        paragraph.text = new_text

def redact_document(doc, mapping_dict):
    """
    Iterates through all paragraphs and table cells in the document to redact PII.
    """
    if not mapping_dict:
        return

    total_paragraphs = len(doc.paragraphs)
    for idx, paragraph in enumerate(doc.paragraphs):
        if idx > 0 and idx % 100 == 0:
            print(f"Processing paragraph {idx}/{total_paragraphs}...")
        redact_paragraph(paragraph, mapping_dict)

    total_tables = len(doc.tables)
    print("Processing tables...")
    for idx, table in enumerate(doc.tables):
        if idx > 0 and idx % 10 == 0:
            print(f"Processing table {idx}/{total_tables}...")
        for cell in table._cells:
            for paragraph in cell.paragraphs:
                redact_paragraph(paragraph, mapping_dict)
