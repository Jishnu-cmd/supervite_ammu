import os
import hashlib
from typing import Dict, Any, List, Tuple
import fitz  # PyMuPDF

class DocumentService:
    @classmethod
    def calculate_file_hash(cls, file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    @classmethod
    def extract_text_and_bboxes(cls, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extracts words and bounding box coordinates [x0, y0, x1, y1] for each page in PDF.
        """
        pages_data = []
        if not os.path.exists(pdf_path):
            return pages_data

        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                words = page.get_text("words")  # List of (x0, y0, x1, y1, word, block_no, line_no, word_no)
                word_objects = []
                for w in words:
                    word_objects.append({
                        "text": w[4],
                        "bbox": [round(w[0], 2), round(w[1], 2), round(w[2], 2), round(w[3], 2)]
                    })
                pages_data.append({
                    "page": page_num + 1,
                    "width": round(page.rect.width, 2),
                    "height": round(page.rect.height, 2),
                    "text": page.get_text("text"),
                    "words": word_objects
                })
            doc.close()
        except Exception as e:
            print(f"Error extracting PDF bboxes: {e}")
            
        return pages_data
