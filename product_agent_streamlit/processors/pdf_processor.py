"""PDF processing module for catalog analysis."""

import json
from io import BytesIO
from typing import List
from PIL import Image
import fitz  # PyMuPDF
import google.generativeai as genai

from models.pdf_metadata import PDFMetadata
from config import GEMINI_MODEL_NAME, PDF_DPI, MAX_ANALYSIS_LENGTH


class PDFCatalogProcessor:
    """Handles PDF processing and analysis using Gemini."""
    
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        
    def pdf_to_images(self, pdf_path: str, dpi: int = PDF_DPI) -> List[Image.Image]:
        """Convert PDF pages to PIL Images for processing."""
        try:
            pdf_document = fitz.open(pdf_path)
            images = []
            
            print(f"Converting {pdf_document.page_count} pages to images...")
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                mat = fitz.Matrix(dpi/72, dpi/72)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(BytesIO(img_data))
                images.append(img)
                print(f"Processed page {page_num + 1}/{pdf_document.page_count}")
            
            pdf_document.close()
            return images
            
        except Exception as e:
            raise Exception(f"Error converting PDF: {str(e)}")
    
    def analyze_catalog_batch(self, images: List[Image.Image], batch_start: int) -> str:
        """Analyze a batch of catalog pages."""
        analysis_prompt = f"""
        You are analyzing pages {batch_start + 1} to {batch_start + len(images)} of a product catalog.
        
        Extract ALL information including:
        - Product names, models, SKUs, and exact product identifiers
        - Complete descriptions and features  
        - Prices and pricing variations
        - Technical specifications and dimensions
        - Categories, sections, and product types
        - Brand names and manufacturers
        - Contact information
        - Special offers or promotions
        - Page numbers for reference
        
        IMPORTANT: Be extremely thorough and extract ALL visible text including text in images.
        Pay special attention to product names and variations.
        
        Format the response as structured data that can be easily searched and referenced.
        Include a product list at the beginning with all product names found.
        """
        
        try:
            response = self.model.generate_content([analysis_prompt] + images)
            return response.text
        except Exception as e:
            return f"Error analyzing batch starting at page {batch_start + 1}: {str(e)}"

    def generate_pdf_metadata(self, images: List[Image.Image], filename: str) -> PDFMetadata:
        """Generate metadata and summary for a PDF catalog."""
        try:
            # Sample first few pages for metadata generation
            sample_images = images[:min(8, len(images))]  # Increased sample size
            
            metadata_prompt = """
            Analyze this product catalog thoroughly and provide metadata in the following JSON format:
            {
                "summary": "Detailed 3-4 sentence summary of what this catalog contains, including specific product types and brands",
                "categories": ["category1", "category2", "category3", "category4", "category5"],
                "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8"],
                "product_types": ["specific_product_type1", "specific_product_type2", "specific_product_type3"],
                "main_business_type": "detailed description of business type",
                "brand_names": ["brand1", "brand2", "brand3"],
                "product_names": ["specific_product_name1", "specific_product_name2", "specific_product_name3"]
            }
            
            Focus on:
            - Exact product names and model numbers
            - Specific product categories (e.g., "glass kettles", "espresso machines", "blenders")
            - Brand names and manufacturers
            - Product features and characteristics
            - Target market or industry
            - Key specializations
            
            Be very specific with product types and names. Avoid generic terms.
            Provide only the JSON response, no other text.
            """
            
            response = self.model.generate_content([metadata_prompt] + sample_images)
            
            # Parse JSON response
            try:
                metadata_json = json.loads(response.text.strip())
                print(f"Generated metadata for {filename}: {metadata_json}")
            except Exception as json_error:
                print(f"JSON parsing error: {json_error}")
                print(f"Raw response: {response.text}")
                # Fallback if JSON parsing fails
                metadata_json = self._get_fallback_metadata(filename)
            
            # Create metadata object
            metadata = PDFMetadata(filename, "")
            metadata.summary = metadata_json.get("summary", f"Product catalog: {filename}")
            metadata.categories = metadata_json.get("categories", ["general"])
            metadata.keywords = metadata_json.get("keywords", [])
            metadata.product_types = metadata_json.get("product_types", [])
            metadata.page_count = len(images)
            metadata.is_processed = True
            
            # Store additional metadata for better search
            metadata.brand_names = metadata_json.get("brand_names", [])
            metadata.product_names = metadata_json.get("product_names", [])
            metadata.main_business_type = metadata_json.get("main_business_type", "retail")
            
            return metadata
            
        except Exception as e:
            print(f"Error generating metadata for {filename}: {str(e)}")
            return self._get_basic_metadata(filename, len(images))

    def _get_fallback_metadata(self, filename: str) -> dict:
        """Get fallback metadata when JSON parsing fails."""
        return {
            "summary": f"Product catalog: {filename}",
            "categories": ["general"],
            "keywords": [filename.replace('.pdf', '').lower()],
            "product_types": ["products"],
            "main_business_type": "retail",
            "brand_names": [],
            "product_names": []
        }

    def _get_basic_metadata(self, filename: str, page_count: int) -> PDFMetadata:
        """Return basic metadata when processing fails."""
        metadata = PDFMetadata(filename, "")
        metadata.summary = f"Product catalog: {filename}"
        metadata.categories = ["general"]
        metadata.keywords = [filename.replace('.pdf', '').lower()]
        metadata.product_types = ["products"]
        metadata.page_count = page_count
        return metadata

    def create_consolidated_catalog_data(self, all_analyses: List[str], catalog_name: str) -> str:
        """Create consolidated catalog data from batch analyses."""
        full_analysis = "\n\n".join(all_analyses)
        
        consolidation_prompt = f"""
        Create a consolidated, well-organized, and highly searchable knowledge base for catalog {catalog_name}.
        
        IMPORTANT REQUIREMENTS:
        1. Extract ALL product names, models, and variations
        2. Create a comprehensive product index at the beginning
        3. Organize by categories and product types
        4. Include ALL specifications, prices, and features
        5. Remove duplicates but keep all unique information
        6. Make it easily searchable for any product query
        
        Original Analysis:
        {full_analysis[:MAX_ANALYSIS_LENGTH]}  # Increased limit for better consolidation
        
        Format as:
        === PRODUCT INDEX ===
        [List all products found with page references]
        
        === DETAILED CATALOG CONTENT ===
        [Organized, searchable content]
        """
        
        try:
            consolidated_response = self.model.generate_content(consolidation_prompt)
            return consolidated_response.text
        except Exception as e:
            print(f"Error creating consolidated data: {str(e)}")
            return full_analysis  # Return original analysis as fallback