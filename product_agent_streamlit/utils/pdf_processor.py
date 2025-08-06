
# File: utils/pdf_processor.py
import fitz
from PIL import Image
from io import BytesIO
from typing import List
import logging

logger = logging.getLogger(__name__)

def pdf_to_images(pdf_path: str, dpi: int = 200) -> List[Image.Image]:
    """Convert PDF pages to PIL Images"""
    try:
        pdf_document = fitz.open(pdf_path)
        images = []
        
        logger.info(f"Converting {pdf_document.page_count} pages to images...")
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            mat = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(BytesIO(img_data))
            images.append(img)
            
            if page_num % 10 == 0:
                logger.info(f"Processed page {page_num + 1}/{pdf_document.page_count}")
        
        pdf_document.close()
        return images
        
    except Exception as e:
        logger.error(f"Error converting PDF: {str(e)}")
        raise