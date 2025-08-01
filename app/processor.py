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
                text = plumber_page.extract_text()
                if text:
                    pages_text[page_key] += text + "\n"
                    print(f"[processor] ✅ Extracted embedded text from page {i+1} ({len(text)} characters)")
                else:
                    print(f"[processor] ⚠️ Embedded text present but plumber could not extract page {i+1}")
            else:
                # Fallback to OCR
                print(f"[processor] 🔍 No embedded text on page {i+1}, using OCR...")
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_lines = reader.readtext(np.array(img), detail=0, paragraph=True)
                ocr_text = "\n".join(ocr_lines)
                pages_text[page_key] += ocr_text + "\n"
                print(f"[processor] ✅ OCR extracted {len(ocr_text)} characters from page {i+1}")

    # Check if any meaningful text was extracted
    all_text = "\n".join(pages_text.values()).strip()
    if not all_text:
        raise ValueError("❌ No text could be extracted from the PDF — possibly scanned or corrupt.")

    # Save to TXT file
    with open(output_txt_path, "w", encoding="utf-8") as f:
        for page_key, text in pages_text.items():
            f.write(f"--- {page_key} ---\n{text}\n")

    print(f"[processor] ✅ Saved extracted text to: {output_txt_path} ({len(all_text)} total characters)")
