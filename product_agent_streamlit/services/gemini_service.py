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
        Analyze this product catalog and extract comprehensive metadata. Focus on being VERY SPECIFIC with product types and keywords.

        Return JSON in this exact format:
        {
            "summary": "Detailed summary of catalog contents, mentioning specific product types, models, and key features",
            "categories": ["specific_category1", "specific_category2", "specific_category3"],
            "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10"],
            "product_types": ["specific_product_type1", "specific_product_type2"],
            "main_business_type": "business description",
            "brand_names": ["brand1", "brand2"],
            "product_names": ["full_product_name1", "full_product_name2"]
        }

        IMPORTANT INSTRUCTIONS:
        - Extract ALL visible product names, model numbers, and variations
        - Include technical terms (voltage, power, speed, capacity, etc.)
        - Include product features (high-velocity, hybrid, electric, manual, etc.)
        - Be specific: use "high-velocity fan" not just "fan"
        - Include synonyms: if you see "fan", also add "cooling", "air circulation"
        - Include specifications: "110V", "220V", "variable speed", etc.

        Return ONLY the JSON, no other text.
        """
        
        try:
            response = self.model.generate_content([metadata_prompt] + sample_images)
            logger.info(f"Raw metadata response for {filename}: {response.text[:500]}...")
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
        TASK: You are a product catalog expert. Analyze this user query and rank ALL catalogs by relevance.

        USER QUERY: "{query}"

        AVAILABLE CATALOGS:
        {catalog_summaries}

        SCORING INSTRUCTIONS:
        Rate each catalog 0-10 based on how well it matches the query:

        10: Perfect match - catalog contains the exact product mentioned
        8-9: Very high - catalog has similar/related products in same category
        6-7: Good match - catalog has products in related category
        4-5: Some relevance - catalog might have tangentially related items
        1-3: Low relevance - minimal connection to query
        0: No relevance - completely unrelated

        SPECIFIC MATCHING CRITERIA:
        - Match specific product names/models mentioned in query
        - Match product categories (e.g., "fan" matches "fans", "cooling", "air circulation")
        - Match technical specifications (e.g., "voltage" matches electrical products)
        - Match brands and manufacturers
        - Match use cases and applications

        EXAMPLES:
        Query: "Hybrid High-Velocity Fan voltage" 
        - Fan catalog: 10 (exact match)
        - Kitchen appliance catalog: 2 (unrelated)
        - Electronics catalog: 4 (voltage is electrical term)

        Return ONLY this JSON format (no extra text):
        [
            {{"catalog": "exact_filename.pdf", "relevance_score": 9, "reason": "Contains high-velocity fan products"}},
            {{"catalog": "exact_filename2.pdf", "relevance_score": 2, "reason": "Only kitchen slicers, no fans"}}
        ]

        Include ALL catalogs. Be strict with scoring - don't give high scores unless there's real relevance.
        """
        
        try:
            response = self.model.generate_content(search_prompt)
            response_text = response.text.strip()
            
            # Clean JSON response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
                
            logger.info(f"Gemini catalog scores: {response_text}")
            return json.loads(response_text.strip())

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error in Gemini catalog search: {e}")
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