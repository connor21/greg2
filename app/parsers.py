from pathlib import Path
from typing import Tuple, Dict
import hashlib

import fitz  # PyMuPDF
from docx import Document as DocxDocument


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def parse_pdf(path: Path) -> Tuple[str, Dict]:
    doc = fitz.open(path)
    texts = []
    for page in doc:
        texts.append(page.get_text())
    text = "\n\n".join(texts)
    meta = {
        "doc_id": path.stem,
        "filename": path.name,
        "mime": "application/pdf",
        "pages": len(doc),
        "hash": _hash_file(path),
        # Include per-page texts for downstream page-aware chunking
        "page_texts": [{"page": i + 1, "text": t} for i, t in enumerate(texts)],
    }
    return text, meta


def parse_docx(path: Path) -> Tuple[str, Dict]:
    d = DocxDocument(path)
    text = "\n".join(p.text for p in d.paragraphs)
    meta = {
        "doc_id": path.stem,
        "filename": path.name,
        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pages": None,
        "hash": _hash_file(path),
    }
    return text, meta


def parse_txt(path: Path) -> Tuple[str, Dict]:
    text = path.read_text(encoding='utf-8', errors='ignore')
    meta = {
        "doc_id": path.stem,
        "filename": path.name,
        "mime": "text/plain",
        "pages": None,
        "hash": _hash_file(path),
    }
    return text, meta


def parse_md(path: Path) -> Tuple[str, Dict]:
    # Treat as plain text for MVP
    return parse_txt(path)


def parse_document(path: Path) -> Tuple[str, Dict]:
    ext = path.suffix.lower()
    if ext == '.pdf':
        return parse_pdf(path)
    if ext == '.docx':
        return parse_docx(path)
    if ext in {'.txt'}:
        return parse_txt(path)
    if ext in {'.md'}:
        return parse_md(path)
    raise ValueError(f"Unsupported file type: {ext}")
