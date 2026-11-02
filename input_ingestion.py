"""Multi-format input helpers for Research Analyzer Professional.

Supports tabular CSV/XLSX/XLS input and text extraction from DOCX/PDF.
Text extraction preserves source/page metadata for qualitative review.
"""
from __future__ import annotations
from io import BytesIO, StringIO
from pathlib import Path
import pandas as pd
from docx import Document
from pypdf import PdfReader

TABULAR_EXTENSIONS = {"csv", "xlsx", "xls"}
TEXT_EXTENSIONS = {"docx", "pdf"}
SUPPORTED_EXTENSIONS = TABULAR_EXTENSIONS | TEXT_EXTENSIONS


def extension_of(uploaded_file) -> str:
    return Path(getattr(uploaded_file, "name", "")).suffix.lower().lstrip(".")


def excel_sheet_names(uploaded_file) -> list[str]:
    ext = extension_of(uploaded_file)
    if ext not in {"xlsx", "xls"}:
        return []
    uploaded_file.seek(0)
    book = pd.ExcelFile(uploaded_file)
    uploaded_file.seek(0)
    return list(book.sheet_names)


def read_tabular(uploaded_file, sheet_name: str | int | None = 0) -> pd.DataFrame:
    ext = extension_of(uploaded_file)
    uploaded_file.seek(0)
    if ext == "csv":
        # utf-8-sig handles Excel-generated CSV; fallback to common Indonesian encodings.
        raw = uploaded_file.getvalue()
        errors = []
        for encoding in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                return pd.read_csv(BytesIO(raw), encoding=encoding)
            except Exception as exc:
                errors.append(str(exc))
        raise ValueError("CSV tidak dapat dibaca. Periksa delimiter dan encoding.")
    if ext in {"xlsx", "xls"}:
        return pd.read_excel(uploaded_file, sheet_name=sheet_name)
    raise ValueError("Format tabel harus CSV, XLSX, atau XLS.")


def extract_docx(uploaded_file) -> list[dict]:
    uploaded_file.seek(0)
    doc = Document(uploaded_file)
    chunks: list[dict] = []
    for i, paragraph in enumerate(doc.paragraphs, start=1):
        text = paragraph.text.strip()
        if text:
            chunks.append({"source": "DOCX", "location": f"Paragraf {i}", "text": text})
    for ti, table in enumerate(doc.tables, start=1):
        for ri, row in enumerate(table.rows, start=1):
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            line = " | ".join(x for x in cells if x)
            if line:
                chunks.append({"source": "DOCX", "location": f"Tabel {ti}, baris {ri}", "text": line})
    return chunks


def extract_pdf(uploaded_file) -> list[dict]:
    uploaded_file.seek(0)
    reader = PdfReader(uploaded_file)
    chunks: list[dict] = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            chunks.append({"source": "PDF", "location": f"Halaman {i}", "text": text})
    return chunks


def extract_qualitative_text(uploaded_file) -> list[dict]:
    ext = extension_of(uploaded_file)
    if ext == "docx":
        return extract_docx(uploaded_file)
    if ext == "pdf":
        return extract_pdf(uploaded_file)
    if ext == "txt":
        uploaded_file.seek(0)
        raw = uploaded_file.getvalue()
        text = raw.decode("utf-8-sig", errors="replace").strip()
        return [{"source": "TXT", "location": "Dokumen", "text": text}] if text else []
    if ext == "md":
        uploaded_file.seek(0)
        raw = uploaded_file.getvalue()
        text = raw.decode("utf-8-sig", errors="replace").strip()
        return [{"source": "MD", "location": "Dokumen", "text": text}] if text else []
    raise ValueError("Dokumen kualitatif harus DOCX, PDF, TXT, atau MD.")
