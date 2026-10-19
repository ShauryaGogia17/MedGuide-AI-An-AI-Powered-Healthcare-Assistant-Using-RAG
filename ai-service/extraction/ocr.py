"""Render only pages without selectable text and OCR locally."""
import os
import shutil
import pypdfium2 as pdfium
import pytesseract

def extract_page_ocr(file_path: str, page_index: int) -> str:
    command = os.getenv('TESSERACT_CMD') or shutil.which('tesseract')
    if not command:
        raise ValueError('This report needs OCR. Install Tesseract or set TESSERACT_CMD, then retry.')
    pytesseract.pytesseract.tesseract_cmd = command
    document = pdfium.PdfDocument(file_path)
    try:
        page = document[page_index]
        try:
            bitmap = page.render(scale=2)
            try:
                image = bitmap.to_pil()
                return pytesseract.image_to_string(image, lang=os.getenv('OCR_LANGUAGE', 'eng'), timeout=45).strip()
            finally:
                bitmap.close()
        finally:
            page.close()
    finally:
        document.close()
