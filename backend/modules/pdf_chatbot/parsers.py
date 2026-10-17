# PDF text extraction (PyPDF/Flitz) & semantic chunking strategies
import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PdfParseError(Exception):
    pass


def extract_pages(data):
    try:

        reader = PdfReader(io.BytesIO(data))
        return [
            (number, page.extract_text() or "")
            for number, page in enumerate(reader.pages, 1)
        ]
    except PdfReadError as exc:
        raise PdfParseError(f"Unreadable PDF: {exc}") from exc


def chunk_pages(pages, size=1000, overlap=200):
    chunks = []
    for page_number, text in pages:
        text = " ".join(text.split())
        start = 0
        while start < len(text):
            chunks.append(
                {
                    "chunk_index": len(chunks),
                    "page_number": page_number,
                    "content": text[start : start + size],
                }
            )
            start += size - overlap
    return chunks
