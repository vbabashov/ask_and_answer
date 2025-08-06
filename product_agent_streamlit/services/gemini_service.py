import google.generativeai as genai
import json
from typing import List, Dict, Any
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for Gemini AI interactions"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def analyze_catalog_batch(self, images: List[Image.Image], batch_start: int) -> str:
        """Analyze a batch of catalog pages"""
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
        - Warranty and support details
        - Page numbers for reference
        
        IMPORTANT: Be extremely thorough and extract ALL visible text including text in images.
        Pay special attention to product names and variations.
        
        Format the response as structured data that can be easily searched and referenced.
        Include a product list at the beginning with all product names found.
        """
        
        try:
            response = self.model.generate_content([analysis_prompt] + images)
            print("This is the response from the extracted content", response.text)
            return response.text
        except Exception as e:
            logger.error(f"Error analyzing batch starting at page {batch_start + 1}: {str(e)}")
            return f"Error analyzing batch starting at page {batch_start + 1}: {str(e)}"

    def generate_metadata(self, images: List[Image.Image], filename: str) -> Dict[str, Any]:
        """Generate metadata for a PDF catalog"""
        sample_images = images[:min(8, len(images))]
        
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
        
        try:
            response = self.model.generate_content([metadata_prompt] + sample_images)
            print("This is the response from the extracted content", response.text)
            return json.loads(response.text.strip())
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Error generating metadata for {filename}: {str(e)}")
            return {
                "summary": f"Product catalog: {filename}",
                "categories": ["general"],
                "keywords": [filename.replace('.pdf', '').lower()],
                "product_types": ["products"],
                "main_business_type": "retail",
                "brand_names": [],
                "product_names": []
            }
    
    def search_catalogs(self, query: str, catalog_summaries: str) -> List[Dict[str, Any]]:
        """Search for relevant catalogs based on query"""
        search_prompt = f"""
        You are a catalog relevance expert. Given this user query: "{query}"
        
        And these available catalogs:
        {catalog_summaries}
        
        TASK: Rank ALL catalogs by relevance to the query (0-10 scale, 10 being most relevant).
        
        SCORING GUIDELINES:
        - 10: Perfect match (exact product mentioned in catalog)
        - 8-9: Very high match (similar products, same category)
        - 6-7: Good match (related products or category)
        - 4-5: Moderate match (some relevance)
        - 1-3: Low match (minimal relevance)
        - 0: No match (completely unrelated)
        
        Return ONLY a JSON array with this exact format:
        [
            {{"catalog": "exact_filename.pdf", "relevance_score": 9, "reason": "Contains Temperature Glass Kettle products"}},
            {{"catalog": "exact_filename2.pdf", "relevance_score": 2, "reason": "Only contains espresso machines, not kettles"}}
        ]
        
        Include ALL catalogs in the response with their scores.
        Return only the JSON, no other text.
        """
        
        try:
            response = self.model.generate_content(search_prompt)
            response_text = response.text.strip()
            
            # Clean JSON response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            print("THIS IS  THE SCORE RESPONSE", response_text )
            return json.loads(response_text.strip())

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error in catalog search: {e}")
            return []

    def consolidate_catalog_content(self, full_analysis: str, catalog_name: str) -> str:
        """Create consolidated catalog knowledge base"""
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
        {full_analysis[:20000]}
        
        Format as:
        === PRODUCT INDEX ===
        [List all products found with page references]
        
        === DETAILED CATALOG CONTENT ===
        [Organized, searchable content]
        """
        
        try:
            response = self.model.generate_content(consolidation_prompt)
            print("THIS IS THE CONSOLIDATION RESPONSE", response.text)
            return response.text
        except Exception as e:
            logger.error(f"Error consolidating catalog content: {str(e)}")
            return full_analysis[:20000]  # Fallback to truncated original

    def search_products(self, query: str, catalog_data: str, catalog_name: str) -> str:
        """Search for products in catalog"""
        search_prompt = f"""
        You are analyzing the catalog "{catalog_name}" for products related to "{query}".
        
        Catalog content:
        {catalog_data[:12000]}
        
        TASK: Search thoroughly for ANY products that match or relate to the query "{query}".
        
        If you find matching products, provide:
        1. All matching products with full details
        2. Exact product names and model numbers
        3. Prices and specifications
        4. Page numbers where found
        5. Why each product matches the search
        6. Features and capabilities
        7. Warranty and support info
        
        If NO matching products are found, respond with:
        "No products matching '{query}' were found in this catalog. This catalog contains [list the main product types you can see]."
        
        Be thorough and accurate. Don't make up information.
        """
        
        try:
            response = self.model.generate_content(search_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return f"Error searching products in {catalog_name}: {str(e)}"