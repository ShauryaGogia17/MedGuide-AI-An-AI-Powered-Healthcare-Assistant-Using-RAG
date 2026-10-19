from pypdf import PdfReader
from extraction.ocr import extract_page_ocr
import os

def extract_pages(file_path: str) -> list[dict]:
    try:
        reader = PdfReader(file_path)
        if reader.is_encrypted:
            raise ValueError('Password-protected PDFs are not supported; upload an unlocked copy')
        if len(reader.pages) > int(os.getenv('MAX_PDF_PAGES', '100')):
            raise ValueError('PDF has too many pages (maximum 100 by default)')
        pages = []
        for index, page in enumerate(reader.pages):
            text = (page.extract_text() or '').strip()
            method = 'text'
            if not text:
                text = extract_page_ocr(file_path, index)
                method = 'ocr'
            if text:
                pages.append({'page': index + 1, 'text': text, 'extraction_method': method})
        if not pages:
            raise ValueError('No readable text was found in this PDF')
        return pages
    except ValueError:
        raise
    except Exception as error:
        raise ValueError('Cannot read this PDF. It may be damaged or OCR may have failed.') from error

def extract_text(file_path: str) -> str:
    return '\n'.join(page['text'] for page in extract_pages(file_path))
