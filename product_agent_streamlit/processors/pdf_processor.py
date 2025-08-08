# pdf_processor.py
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
import google.generativeai as genai
from typing import List

class PDFProcessor:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """Convert PDF to images."""
        try:
            pdf_document = fitz.open(pdf_path)
            images = []
            
            for page_num in range(min(pdf_document.page_count, 20)):  # Limit to 20 pages
                page = pdf_document[page_num]
                mat = fitz.Matrix(150/72, 150/72)  # Lower DPI for efficiency
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(BytesIO(img_data))
                images.append(img)
            
            pdf_document.close()
            return images
        except Exception as e:
            raise Exception(f"Error converting PDF: {str(e)}")
    
    def extract_full_content(self, images: List[Image.Image]) -> str:
        """Extract complete content from PDF images."""
        batch_size = 3
        all_content = []
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            
            prompt = f"""
            Extract ALL text and product information from these catalog pages.
            
            Include:
            - Product names and model numbers
            - Specifications and dimensions  
            - Prices and part numbers
            - Instructions and descriptions
            - Warranty information
            - Company details
            
            Format as clear, structured text with product sections.
            """
            
            try:
                response = self.model.generate_content([prompt] + batch)
                if hasattr(response, 'text') and response.text:
                    all_content.append(f"=== Pages {i+1}-{min(i+batch_size, len(images))} ===\n{response.text}")
            except Exception as e:
                all_content.append(f"Error extracting pages {i+1}-{min(i+batch_size, len(images))}: {str(e)}")
        
        return "\n\n".join(all_content)
    
    def generate_summary(self, images: List[Image.Image], filename: str) -> str:
        """Generate catalog summary for selection."""
        sample_images = images[:min(5, len(images))]
        
        prompt = f"""
        Analyze this catalog and create a brief summary.
        
        Include:
        - Main product categories
        - Types of products offered
        - Target market/industry
        - Key brands if visible
        - Specializations
        
        Keep it concise (2-3 sentences) but specific enough to distinguish from other catalogs.
        """
        
        try:
            response = self.model.generate_content([prompt] + sample_images)
            if hasattr(response, 'text') and response.text:
                return response.text
            return f"Product catalog: {filename}"
        except Exception as e:
            return f"Product catalog: {filename} - Summary generation failed"