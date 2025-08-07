# """
# Tools for the individual catalog agent
# """

# from typing import List
# from PIL import Image
# from processors.pdf_processor import PDFCatalogProcessor

# class CatalogTools:
#     """Tools for the individual catalog agent."""
    
#     def __init__(self, catalog_data: str, pdf_images: List[Image.Image], processor: PDFCatalogProcessor, catalog_name: str):
#         self.catalog_data = catalog_data
#         self.pdf_images = pdf_images
#         self.processor = processor
#         self.catalog_name = catalog_name
    
#     async def search_products(self, query: str) -> str:
#         """Search for products in the catalog based on query."""
#         try:
#             print(f"\n=== CATALOG AGENT SEARCH ===")
#             print(f"Catalog: {self.catalog_name}")
#             print(f"Query: {query}")
#             print(f"Catalog data preview: {self.catalog_data[:500]}...")
            
#             search_prompt = f"""
#             You are analyzing the catalog "{self.catalog_name}" for products related to "{query}".
            
#             Catalog content:
#             {self.catalog_data[:12000]}  # Increased context window
            
#             TASK: Search thoroughly for ANY products that match or relate to the query "{query}".
            
#             If you find matching products, provide:
#             1. All matching products with full details
#             2. Exact product names and model numbers
#             3. Prices and specifications
#             4. Page numbers where found
#             5. Why each product matches the search
#             6. Features and capabilities
#             7. Warranty and support info
            
#             If NO matching products are found, respond with:
#             "No products matching '{query}' were found in this catalog. This catalog contains [list the main product types you can see]."
            
#             Be thorough and accurate. Don't make up information.
#             """
            
#             response = self.processor.model.generate_content(search_prompt)
#             result = response.text
#             print(f"Search result: {result[:200]}...")
#             return result
            
#         except Exception as e:
#             return f"Error searching products in {self.catalog_name}: {str(e)}"
    
#     async def get_product_details(self, product_name: str) -> str:
#         """Get detailed information about a specific product."""
#         try:
#             detail_prompt = f"""
#             From catalog {self.catalog_name}, find detailed information about "{product_name}":
            
#             {self.catalog_data[:8000]}
            
#             Provide complete details including:
#             - Full product name and model
#             - All specifications and features
#             - Price and pricing options
#             - Page location
#             - Category/section
#             - Related products
#             - Availability information
            
#             If exact product not found, suggest closest matches.
#             """
            
#             response = self.processor.model.generate_content(detail_prompt)
#             return response.text
            
#         except Exception as e:
#             return f"Error getting product details: {str(e)}"
    
#     async def compare_products(self, product1: str, product2: str) -> str:
#         """Compare two products from the catalog."""
#         try:
#             compare_prompt = f"""
#             From catalog {self.catalog_name}, compare "{product1}" and "{product2}":
            
#             {self.catalog_data[:8000]}
            
#             Provide:
#             1. Side-by-side comparison table
#             2. Price comparison
#             3. Feature differences
#             4. Pros and cons for each
#             5. Recommendations for different use cases
#             6. Page references
            
#             If products not found, suggest similar alternatives.
#             """
            
#             response = self.processor.model.generate_content(compare_prompt)
#             return response.text
            
#         except Exception as e:
#             return f"Error comparing products: {str(e)}"
    
#     async def analyze_specific_pages(self, page_numbers: str, focus: str = "general analysis") -> str:
#         """Analyze specific pages with focused attention."""
#         try:
#             pages = [int(p.strip()) for p in page_numbers.split(',') if p.strip().isdigit()]
#             valid_pages = [i-1 for i in pages if 0 < i <= len(self.pdf_images)]
            
#             if not valid_pages:
#                 return "No valid page numbers provided. Please specify page numbers separated by commas."
            
#             pages_to_analyze = [self.pdf_images[i] for i in valid_pages]
            
#             analyze_prompt = f"""
#             Analyze pages {page_numbers} from catalog {self.catalog_name} with focus on: {focus}
            
#             Extract:
#             1. All products on these pages
#             2. Complete text content
#             3. Pricing and specifications
#             4. Special offers or promotions
#             5. Technical details
#             6. Contact/ordering information
            
#             Focus area: {focus}
#             Be thorough and extract all visible text.
#             """
            
#             response = self.processor.model.generate_content([analyze_prompt] + pages_to_analyze)
#             return response.text
            
#         except Exception as e:
#             return f"Error analyzing pages: {str(e)}"
    
#     async def get_catalog_overview(self) -> str:
#         """Get overview of the catalog."""
#         try:
#             overview_prompt = f"""
#             Provide a comprehensive overview of catalog {self.catalog_name}:
            
#             {self.catalog_data[:8000]}
            
#             Include:
#             1. Business type and product categories
#             2. Total number of products
#             3. Price ranges
#             4. Main sections/categories  
#             5. Special features or highlights
#             6. Contact and ordering information
#             7. List of main product names/types available
            
#             Keep it informative but concise.
#             """
            
#             response = self.processor.model.generate_content(overview_prompt)
#             return response.text
            
#         except Exception as e:
#             return f"Error generating overview: {str(e)}"

"""
Enhanced tools for individual catalog agents with better product search
Key improvements:
1. Multi-stage search with different strategies
2. Better product matching and extraction
3. Enhanced search prompt engineering
4. Improved fallback mechanisms
"""

from typing import List
from PIL import Image
from processors.pdf_processor import PDFCatalogProcessor
import re

class CatalogTools:
    """Enhanced tools for individual catalog agents."""
    
    def __init__(self, catalog_data: str, pdf_images: List[Image.Image], processor: PDFCatalogProcessor, 
                 catalog_name: str, product_index: str = "", catalog_summary: str = ""):
        self.catalog_data = catalog_data
        self.pdf_images = pdf_images
        self.processor = processor
        self.catalog_name = catalog_name
        self.product_index = product_index
        self.catalog_summary = catalog_summary
    
    async def search_products(self, query: str) -> str:
        """Enhanced multi-stage product search."""
        try:
            print(f"\\n=== ENHANCED CATALOG SEARCH ===")
            print(f"Catalog: {self.catalog_name}")
            print(f"Query: {query}")
            print(f"Data available: {len(self.catalog_data)} chars, Index: {len(self.product_index)} chars")
            
            # Stage 1: Direct keyword search in product index
            if self.product_index:
                index_result = await self._search_in_product_index(query)
                if self._is_good_search_result(index_result, query):
                    print("✅ Found good result in product index")
                    return self._format_response(index_result, "Product Index Search")
            
            # Stage 2: Comprehensive catalog search with focused prompts
            catalog_result = await self._search_in_catalog_data(query)
            if self._is_good_search_result(catalog_result, query):
                print("✅ Found good result in catalog data")
                return self._format_response(catalog_result, "Catalog Data Search")
            
            # Stage 3: Fuzzy/related product search
            related_result = await self._search_related_products(query)
            if self._is_good_search_result(related_result, query):
                print("✅ Found related products")
                return self._format_response(related_result, "Related Product Search")
            
            # Stage 4: Category-based search
            category_result = await self._search_by_category(query)
            if self._is_good_search_result(category_result, query):
                print("✅ Found results by category")
                return self._format_response(category_result, "Category Search")
            
            # Stage 5: Return best available result or helpful message
            best_result = catalog_result or index_result or related_result or category_result
            if best_result:
                return self._format_response(best_result, "Best Available Match")
            else:
                return await self._generate_helpful_response(query)
            
        except Exception as e:
            return f"❌ Error searching products in {self.catalog_name}: {str(e)}"
    
    async def _search_in_product_index(self, query: str) -> str:
        """Search within the product index for quick matches."""
        if not self.product_index:
            return ""
        
        search_prompt = f"""
        Search this product index for products related to: "{query}"
        
        PRODUCT INDEX:
        {self.product_index[:8000]}
        
        TASK: Find ALL products that match or relate to the query "{query}".
        
        Look for:
        - Exact product name matches
        - Model number matches  
        - Category matches
        - Feature matches
        - Similar or related products
        
        If matches found, provide:
        - Complete product names and models
        - All pricing information
        - Page references
        - Key specifications
        - Why each product matches
        
        If NO matches, clearly state: "No matching products found in index."
        
        Be thorough and accurate. Include ALL relevant matches.
        """
        
        try:
            response = self.processor.model.generate_content(search_prompt)
            result = response.text.strip()
            print(f"Index search result preview: {result[:200]}...")
            return result
        except Exception as e:
            print(f"Index search error: {e}")
            return ""
    
    async def _search_in_catalog_data(self, query: str) -> str:
        """Search within the main catalog data."""
        search_prompt = f"""
        You are searching catalog "{self.catalog_name}" for: "{query}"
        
        CATALOG CONTENT:
        {self.catalog_data[:15000]}  # Increased context
        
        SEARCH REQUIREMENTS:
        1. Find ALL products matching or related to "{query}"
        2. Include exact product names and model numbers
        3. Provide complete specifications and features
        4. Include ALL pricing information found
        5. Note page numbers for reference
        6. Explain why each product matches the search
        
        RESPONSE FORMAT:
        **MATCHING PRODUCTS:**
        1. [Product Name] - [Model] - $[Price]
           - Specifications: [details]
           - Features: [key features]
           - Page: [page number]
           - Match reason: [why it matches the search]
        
        **ADDITIONAL DETAILS:**
        [Any additional relevant information]
        
        If NO matching products found, state clearly:
        "No products matching '{query}' found in this catalog."
        Then list what product categories ARE available.
        
        Be extremely thorough and accurate.
        """
        
        try:
            response = self.processor.model.generate_content(search_prompt)
            result = response.text.strip()
            print(f"Catalog search result preview: {result[:200]}...")
            return result
        except Exception as e:
            print(f"Catalog search error: {e}")
            return ""
    
    async def _search_related_products(self, query: str) -> str:
        """Search for related or similar products when exact matches fail."""
        search_prompt = f"""
        The user searched for "{query}" in catalog "{self.catalog_name}".
        No exact matches were found. Now search for RELATED or SIMILAR products.
        
        CATALOG CONTENT:
        {self.catalog_data[:12000]}
        
        SEARCH STRATEGY:
        1. Break down the query into key concepts
        2. Look for products in the same category
        3. Find products with similar functions or features
        4. Consider alternative names or synonyms
        5. Look for products that could serve similar purposes
        
        PROVIDE:
        - Related products with explanations of similarity
        - Alternative products that might meet user needs
        - Products in similar categories
        - Clear explanation of why these are related
        
        FORMAT:
        **RELATED PRODUCTS FOR '{query}':**
        
        **Similar Products:**
        [List products with explanations of similarity]
        
        **Alternative Solutions:**
        [Products that might serve similar purposes]
        
        **Same Category:**
        [Products in related categories]
        
        If NO related products exist, clearly explain what categories and products ARE available.
        """
        
        try:
            response = self.processor.model.generate_content(search_prompt)
            result = response.text.strip()
            print(f"Related search result preview: {result[:200]}...")
            return result
        except Exception as e:
            print(f"Related search error: {e}")
            return ""
    
    async def _search_by_category(self, query: str) -> str:
        """Search by inferring category from the query."""
        search_prompt = f"""
        Analyze the query "{query}" to determine what CATEGORY of products the user wants.
        Then show ALL products in that category from catalog "{self.catalog_name}".
        
        CATALOG CONTENT:
        {self.catalog_data[:12000]}
        
        STEPS:
        1. Determine the likely product category from "{query}"
        2. Find ALL products in that category
        3. Present them with full details
        
        EXAMPLE:
        Query: "coffee makers" → Category: "Kitchen Appliances" or "Coffee Equipment"
        Query: "laptop computers" → Category: "Electronics" or "Computers"
        
        PROVIDE:
        **CATEGORY ANALYSIS FOR '{query}':**
        Determined Category: [category name]
        
        **ALL PRODUCTS IN THIS CATEGORY:**
        [Complete list with details, prices, pages]
        
        **RELATED CATEGORIES:**
        [Other relevant categories available]
        
        Be comprehensive - show ALL products in the determined category.
        """
        
        try:
            response = self.processor.model.generate_content(search_prompt)
            result = response.text.strip()
            print(f"Category search result preview: {result[:200]}...")
            return result
        except Exception as e:
            print(f"Category search error: {e}")
            return ""
    
    def _is_good_search_result(self, result: str, query: str) -> bool:
        """Determine if a search result is useful."""
        if not result or len(result.strip()) < 30:
            return False
        
        result_lower = result.lower()
        query_lower = query.lower()
        
        # Negative indicators
        negative_patterns = [
            "no products matching",
            "no matching products",
            "not found",
            "no information",
            "unable to find",
            "error"
        ]
        
        # Check for negative indicators
        has_negative = any(pattern in result_lower for pattern in negative_patterns)
        
        # Positive indicators
        positive_patterns = [
            "$",  # Price
            "price:",
            "model:",
            "page:",
            "specification",
            "feature",
            "product name",
            "available"
        ]
        
        has_positive = any(pattern in result_lower for pattern in positive_patterns)
        
        # Check if query terms appear in result
        query_words = [word for word in query_lower.split() if len(word) > 3]
        query_terms_present = any(word in result_lower for word in query_words) if query_words else False
        
        # Good result should have positive indicators and query relevance
        return (has_positive or query_terms_present) and not has_negative and len(result.strip()) > 100
    
    def _format_response(self, response: str, search_method: str) -> str:
        """Format the search response with catalog information."""
        formatted = f"**Search Results from {self.catalog_name}** (Method: {search_method})\\n\\n"
        formatted += response
        formatted += f"\\n\\n*Source: {self.catalog_name}*"
        return formatted
    
    async def _generate_helpful_response(self, query