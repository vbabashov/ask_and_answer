"""
Enhanced PDF processing with better metadata extraction
Key improvements:
1. More thorough product name extraction
2. Better categorization
3. Enhanced keyword generation
4. Improved brand detection
"""

import json
from typing import List
from io import BytesIO
import fitz  # PyMuPDF
from PIL import Image
import google.generativeai as genai
import re

from models.pdf_metadata import PDFMetadata

class PDFCatalogProcessor:
    """Handles PDF processing and analysis using Gemini."""
    
    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key  # Store the API keys
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def pdf_to_images(self, pdf_path: str, dpi: int = 200) -> List[Image.Image]:
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
                if (page_num + 1) % 10 == 0:  # Progress indicator
                    print(f"Processed {page_num + 1}/{pdf_document.page_count} pages")
            
            pdf_document.close()
            return images
            
        except Exception as e:
            raise Exception(f"Error converting PDF: {str(e)}")
    
    def analyze_catalog_batch(self, images: List[Image.Image], batch_start: int) -> str:
        """Analyze a batch of catalog pages with enhanced extraction."""
        analysis_prompt = f"""
        Analyze pages {batch_start + 1} to {batch_start + len(images)} of this product catalog.
        
        Extract ALL information with maximum detail:
        
        1. PRODUCTS (Most Important):
           - Extract EVERY product name, model number, SKU, and variant
           - Include full product descriptions
           - Note exact product specifications
           - List all pricing information
        
        2. CATEGORIES & ORGANIZATION:
           - Identify main sections and subsections
           - Note category headers and organization
        
        3. BRANDS & MANUFACTURERS:
           - Extract all brand names and manufacturers
           - Note company information and logos
        
        4. TECHNICAL DETAILS:
           - Specifications, dimensions, features
           - Warranty and support information
        
        5. CONTACT & ORDERING:
           - Company details, contact information
           - Ordering processes and codes
        
        CRITICAL: Extract ALL visible text including small text, captions, and footnotes.
        Create a comprehensive inventory of EVERY product mentioned.
        
        Format as structured, searchable content with clear product listings.
        Start with a detailed product index.
        """
        
        try:
            response = self.model.generate_content([analysis_prompt] + images)
            return response.text
        except Exception as e:
            return f"Error analyzing batch starting at page {batch_start + 1}: {str(e)}"

    def generate_pdf_metadata(self, images: List[Image.Image], filename: str) -> PDFMetadata:
        """Generate enhanced metadata for better catalog differentiation."""
        try:
            # Use more pages for better metadata (up to 12 pages)
            sample_images = images[:min(12, len(images))]
            
            # First pass: Extract all visible text and products
            extraction_prompt = """
            Analyze this product catalog comprehensively and extract:
            
            1. ALL product names (be extremely thorough)
            2. ALL brand names and manufacturers
            3. Main product categories and types
            4. Key features and specializations
            5. Target market or industry focus
            6. Company name and business type
            
            Focus on creating a complete inventory of products and brands.
            Extract even partial product names and model numbers.
            Be very specific - avoid generic terms.
            """
            
            extraction_response = self.model.generate_content([extraction_prompt] + sample_images)
            extraction_text = extraction_response.text
            
            print(f"Extraction text preview for {filename}:")
            print(extraction_text[:500])
            
            # Second pass: Generate structured metadata
            metadata_prompt = f"""
            Based on this catalog analysis:
            {extraction_text[:8000]}
            
            Generate metadata in this EXACT JSON format:
            {{
                "summary": "Detailed 3-4 sentence description of this specific catalog's contents and specialization",
                "categories": ["specific_category1", "specific_category2", "specific_category3", "specific_category4"],
                "product_types": ["specific_product_type1", "specific_product_type2", "specific_product_type3", "specific_product_type4"],
                "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10"],
                "brand_names": ["brand1", "brand2", "brand3", "brand4"],
                "product_names": ["product1", "product2", "product3", "product4", "product5", "product6", "product7", "product8"]
            }}
            
            REQUIREMENTS:
            - Be very specific with product names (include models, variants)
            - Use exact terminology from the catalog
            - Make categories distinctive (not generic like "products")
            - Include ALL major brands found
            - Keywords should be searchable terms customers would use
            - Product names should be comprehensive and specific
            
            This catalog should be easily distinguishable from other catalogs.
            Return ONLY the JSON, no other text.
            """
            
            response = self.model.generate_content(metadata_prompt)
            
            # Parse JSON response with better error handling
            try:
                response_text = response.text.strip()
                # Clean up common JSON formatting issues
                if response_text.startswith('```json'):
                    response_text = response_text[7:-3]
                elif response_text.startswith('```'):
                    response_text = response_text[3:-3]
                
                metadata_json = json.loads(response_text)
                print(f"Successfully parsed metadata for {filename}")
                
            except json.JSONDecodeError as json_error:
                print(f"JSON parsing error for {filename}: {json_error}")
                print(f"Raw response: {response.text}")
                
                # Fallback: Extract information using regex
                metadata_json = self._extract_metadata_fallback(extraction_text, filename)
            
            # Create enhanced metadata object
            metadata = PDFMetadata(filename, "")
            metadata.summary = metadata_json.get("summary", f"Product catalog: {filename}")
            metadata.categories = metadata_json.get("categories", [])[:10]  # Limit to 10
            metadata.keywords = metadata_json.get("keywords", [])[:15]  # Limit to 15
            metadata.product_types = metadata_json.get("product_types", [])[:8]  # Limit to 8
            metadata.brand_names = metadata_json.get("brand_names", [])[:10]  # Limit to 10
            metadata.product_names = metadata_json.get("product_names", [])[:20]  # Limit to 20
            metadata.page_count = len(images)
            metadata.is_processed = True
            
            # Add filename-based keywords as fallback
            filename_keywords = self._extract_filename_keywords(filename)
            metadata.keywords.extend(filename_keywords)
            metadata.keywords = list(set(metadata.keywords))[:15]  # Remove duplicates and limit
            
            return metadata
            
        except Exception as e:
            print(f"Error generating metadata for {filename}: {str(e)}")
            return self._create_basic_metadata(filename, len(images))
    
    def _extract_metadata_fallback(self, extraction_text: str, filename: str) -> dict:
        """Fallback method to extract metadata using text analysis."""
        print(f"Using fallback metadata extraction for {filename}")
        
        text_lower = extraction_text.lower()
        
        # Extract potential product names (capitalized words/phrases)
        product_pattern = r'\b[A-Z][a-zA-Z\s\-0-9]{3,30}\b'
        potential_products = re.findall(product_pattern, extraction_text)
        product_names = list(set(potential_products[:15]))  # Remove duplicates
        
        # Extract potential brands (common brand indicators)
        brand_indicators = ['inc', 'corp', 'ltd', 'llc', 'company', 'industries']
        potential_brands = []
        for word in extraction_text.split():
            if any(indicator in word.lower() for indicator in brand_indicators):
                context_words = extraction_text.split()
                try:
                    idx = extraction_text.split().index(word)
                    if idx > 0:
                        potential_brands.append(context_words[idx-1])
                except:
                    pass
        
        # Generate categories based on common product terms
        category_terms = {
            'electronics': ['electronic', 'digital', 'tech', 'device'],
            'appliances': ['appliance', 'kitchen', 'home'],
            'tools': ['tool', 'equipment', 'machine'],
            'furniture': ['furniture', 'chair', 'table', 'desk'],
            'clothing': ['clothing', 'apparel', 'fashion'],
            'automotive': ['auto', 'car', 'vehicle', 'motor'],
        }
        
        categories = []
        for category, terms in category_terms.items():
            if any(term in text_lower for term in terms):
                categories.append(category)
        
        # Generate keywords from text
        common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an']
        words = re.findall(r'\b\w{4,}\b', text_lower)
        keywords = [word for word in set(words) if word not in common_words][:10]
        
        return {
            "summary": f"Product catalog containing {len(product_names)} products",
            "categories": categories[:5] if categories else ["general"],
            "product_types": list(set([name.split()[0].lower() for name in product_names if name.split()]))[:5],
            "keywords": keywords,
            "brand_names": list(set(potential_brands[:5])),
            "product_names": product_names[:10]
        }
    
    def _extract_filename_keywords(self, filename: str) -> List[str]:
        """Extract keywords from filename."""
        # Remove extension and common separators
        name_part = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        words = re.findall(r'\b\w{3,}\b', name_part.lower())
        return words[:5]  # Limit to 5 filename-based keywords
    
    def _create_basic_metadata(self, filename: str, page_count: int) -> PDFMetadata:
        """Create basic metadata when extraction fails."""
        print(f"Creating basic metadata for {filename}")
        
        metadata = PDFMetadata(filename, "")
        metadata.summary = f"Product catalog: {filename}"
        metadata.categories = ["general"]
        metadata.keywords = self._extract_filename_keywords(filename)
        metadata.product_types = ["products"]
        metadata.page_count = page_count
        metadata.brand_names = []
        metadata.product_names = []
        metadata.is_processed = True
        
        return metadata