import os
import fitz  # PyMuPDF
import pdfplumber
import easyocr
from PIL import Image
import numpy as np
import io

# Initialize EasyOCR once
reader = easyocr.Reader(['en'])

def extract_pdf_to_text(pdf_path: str, output_txt_path: str) -> None:
    doc = fitz.open(pdf_path)
    pages_text = {}

    with pdfplumber.open(pdf_path) as plumber_pdf:
        for i in range(len(doc)):
            page = doc[i]
            embedded_text = page.get_text().strip()
            page_key = f"Page_{i+1}"
            pages_text[page_key] = ""

            if embedded_text:
                plumber_page = plumber_pdf.pages[i]

                # --- Text Extraction ---
                text = plumber_page.extract_text()
                if text:
                    pages_text[page_key] += text + "\n"

            else:
                # --- OCR Fallback ---
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_lines = reader.readtext(np.array(img), detail=0, paragraph=True)
                pages_text[page_key] += "\n".join(ocr_lines) + "\n"

    # Save to TXT file
    with open(output_txt_path, "w", encoding="utf-8") as f:
        for page_key, text in pages_text.items():
            f.write(f"--- {page_key} ---\n{text}\n")
