from io import BytesIO

from pypdf import PdfReader

MAX_PAGES = 10      # read only the first 10 pages of a PDF
MAX_CHARS = 12000   # send at most this much text to the AI


def extract_pdf_text(data: bytes) -> str:
    """Take the raw bytes of a PDF and return the text inside it.
    Raises ValueError with a message the app can show to the user."""
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise ValueError("This PDF is password protected.")
        pages = reader.pages[:MAX_PAGES]
        text = "\n".join((page.extract_text() or "") for page in pages)
    except ValueError:
        raise  # our own message above, pass it on unchanged
    except Exception:
        raise ValueError("This PDF could not be read.")

    # tidy: strip each line, drop empty lines
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    if not text:
        raise ValueError("No text found in this PDF. It may be a scanned image.")
    return text[:MAX_CHARS]