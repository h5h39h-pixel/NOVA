# -*- coding: utf-8 -*-
"""File text extraction + chunking — turn an uploaded file (txt/md/pdf/docx/image)
into plain text, and split text into overlapping chunks for embedding. Used by the
upload flow and the knowledge base. Depends only on config (TOOLKIT for OCR)."""
import subprocess
from pathlib import Path
from config import TOOLKIT


def extract_text(path: Path):
    ext = path.suffix.lower()
    try:
        if ext in (".txt", ".md", ".json", ".csv", ".log", ".py", ".js", ".ps1"):
            return path.read_text(encoding="utf-8", errors="replace")
        if ext == ".pdf":
            import pypdf
            r = pypdf.PdfReader(str(path))
            return "\n".join((pg.extract_text() or "") for pg in r.pages)
        if ext == ".docx":
            import docx
            return "\n".join(p.text for p in docx.Document(str(path)).paragraphs)
        if ext in (".png", ".jpg", ".jpeg", ".bmp", ".webp"):
            out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                  "-File", str(TOOLKIT / "ocr.ps1"), str(path)],
                                 capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
            return (out.stdout or "").strip() or "(image attached; no text detected)"
    except Exception as e:
        return f"(could not extract text: {e})"
    return "(unsupported file type)"


def chunk_text(text, size=900, overlap=150):
    text = " ".join((text or "").split())
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i+size]); i += max(1, size - overlap)
    return [c for c in out if c.strip()][:400]
