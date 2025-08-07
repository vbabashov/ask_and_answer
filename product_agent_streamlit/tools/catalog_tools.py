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
            print(f"\n=== ENHANCED CATALOG SEARCH ===")
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
        formatted = f"**Search Results from {self.catalog_name}** (Method: {search_method})\n\n"
        formatted += response
        formatted += f"\n\n*Source: {self.catalog_name}*"
        return formatted
    
    async def _generate_helpful_response(self, query: str) -> str:
        """Generate a helpful response when no products are found."""
        try:
            helpful_prompt = f"""
            The user searched for "{query}" in catalog "{self.catalog_name}" but no matching products were found.
            
            CATALOG OVERVIEW:
            {self.catalog_summary[:1000]}
            
            AVAILABLE CONTENT PREVIEW:
            {self.catalog_data[:3000]}
            
            Create a helpful response that:
            1. Clearly states that the specific query "{query}" was not found
            2. Lists what product categories ARE available in this catalog
            3. Suggests alternative search terms or related products
            4. Shows a few example products from the catalog
            5. Offers to help with more specific queries
            
            FORMAT:
            **Search Result for '{query}' in {self.catalog_name}:**
            
            I couldn't find specific products matching "{query}" in this catalog.
            
            **What's Available in {self.catalog_name}:**
            - [List main product categories]
            - [List some example products]
            
            **Suggestions:**
            - Try searching for: [alternative terms]
            - You might be interested in: [related products]
            
            **Need Help?** Ask me about specific product categories or brands available in this catalog.
            
            Be helpful and informative, not apologetic.
            """
            
            response = self.processor.model.generate_content(helpful_prompt)
            result = response.text.strip()
            return self._format_response(result, "Helpful Response")
            
        except Exception as e:
            return f"❌ Unable to find '{query}' in catalog {self.catalog_name}. Please try a different search term or check other catalogs."
    
    async def get_product_details(self, product_name: str) -> str:
        """Get detailed information about a specific product."""
        try:
            print(f"\n=== PRODUCT DETAILS REQUEST ===")
            print(f"Catalog: {self.catalog_name}")
            print(f"Product: {product_name}")
            
            detail_prompt = f"""
            Find detailed information about product "{product_name}" in catalog "{self.catalog_name}".
            
            SEARCH IN:
            1. Product Index: {self.product_index[:5000]}
            2. Catalog Data: {self.catalog_data[:10000]}
            
            PROVIDE COMPLETE DETAILS:
            - Full product name and all model variations
            - Complete specifications and technical details
            - ALL pricing information (regular, sale, bulk, etc.)
            - Features and capabilities
            - Dimensions, weight, and physical specs
            - Warranty and support information
            - Page number(s) where found
            - Category and section location
            - Related or compatible products
            - Installation or usage requirements
            
            FORMAT:
            **PRODUCT DETAILS: {product_name}**
            
            **Basic Information:**
            - Name: [exact name]
            - Model(s): [all variants]
            - Category: [product category]
            - Page(s): [page references]
            
            **Specifications:**
            [Complete technical details]
            
            **Pricing:**
            [All pricing information found]
            
            **Features:**
            [Key features and capabilities]
            
            **Additional Information:**
            [Warranty, support, related products]
            
            If product not found, suggest closest matches and alternatives.
            Be extremely thorough and accurate.
            """
            
            response = self.processor.model.generate_content(detail_prompt)
            result = response.text.strip()
            return self._format_response(result, "Product Details")
            
        except Exception as e:
            return f"❌ Error getting product details for '{product_name}': {str(e)}"
    
    async def compare_products(self, product1: str, product2: str) -> str:
        """Compare two products from the catalog."""
        try:
            print(f"\n=== PRODUCT COMPARISON ===")
            print(f"Catalog: {self.catalog_name}")
            print(f"Products: {product1} vs {product2}")
            
            compare_prompt = f"""
            Compare products "{product1}" and "{product2}" from catalog "{self.catalog_name}".
            
            CATALOG DATA:
            {self.catalog_data[:12000]}
            
            PRODUCT INDEX:
            {self.product_index[:6000]}
            
            CREATE DETAILED COMPARISON:
            
            **PRODUCT COMPARISON: {product1} vs {product2}**
            
            **Product 1: {product1}**
            - Model/SKU: [model info]
            - Price: [pricing]
            - Key Features: [main features]
            - Specifications: [technical specs]
            - Page: [page reference]
            
            **Product 2: {product2}**
            - Model/SKU: [model info]  
            - Price: [pricing]
            - Key Features: [main features]
            - Specifications: [technical specs]
            - Page: [page reference]
            
            **SIDE-BY-SIDE COMPARISON:**
            | Feature | {product1} | {product2} |
            |---------|------------|------------|
            | Price | [price1] | [price2] |
            | [Feature] | [details] | [details] |
            | [Feature] | [details] | [details] |
            
            **ADVANTAGES:**
            - {product1}: [key advantages]
            - {product2}: [key advantages]
            
            **RECOMMENDATIONS:**
            - Best for [use case]: [product choice and why]
            - Best value: [analysis]
            - Best features: [analysis]
            
            If either product not found, suggest alternatives and explain what's available.
            """
            
            response = self.processor.model.generate_content(compare_prompt)
            result = response.text.strip()
            return self._format_response(result, "Product Comparison")
            
        except Exception as e:
            return f"❌ Error comparing products: {str(e)}"
    
    async def analyze_specific_pages(self, page_numbers: str, focus: str = "general analysis") -> str:
        """Analyze specific pages with focused attention."""
        try:
            print(f"\n=== PAGE ANALYSIS ===")
            print(f"Catalog: {self.catalog_name}")
            print(f"Pages: {page_numbers}")
            print(f"Focus: {focus}")
            
            # Parse page numbers
            pages = []
            for p in page_numbers.replace(' ', '').split(','):
                if '-' in p:  # Handle ranges like "1-5"
                    start, end = map(int, p.split('-'))
                    pages.extend(range(start, end + 1))
                elif p.strip().isdigit():
                    pages.append(int(p.strip()))
            
            # Filter valid pages (1-indexed to 0-indexed)
            valid_pages = [i-1 for i in pages if 0 < i <= len(self.pdf_images)]
            
            if not valid_pages:
                return f"❌ No valid page numbers provided. This catalog has {len(self.pdf_images)} pages. Please specify page numbers like '1,2,3' or '1-5'."
            
            # Get images for analysis
            pages_to_analyze = [self.pdf_images[i] for i in valid_pages]
            actual_pages = [i+1 for i in valid_pages]  # Convert back to 1-indexed for display
            
            analyze_prompt = f"""
            Analyze pages {', '.join(map(str, actual_pages))} from catalog "{self.catalog_name}".
            Focus area: {focus}
            
            EXTRACT EVERYTHING VISIBLE:
            1. **ALL PRODUCTS** on these pages
               - Complete product names and models
               - All pricing information
               - Specifications and features
               - SKUs and part numbers
            
            2. **COMPLETE TEXT CONTENT**
               - Headers and section titles
               - Product descriptions
               - Technical specifications
               - Warranty information
               - Contact details
            
            3. **SPECIAL FOCUS: {focus}**
               - Pay special attention to information related to: {focus}
               - Highlight relevant details for this focus area
            
            4. **ORGANIZATION**
               - How the pages are structured
               - Categories and sections
               - Cross-references to other pages
            
            FORMAT:
            **ANALYSIS OF PAGES {', '.join(map(str, actual_pages))} - FOCUS: {focus.upper()}**
            
            **PRODUCTS FOUND:**
            [Complete list of all products with details]
            
            **KEY INFORMATION:**
            [All relevant text and details]
            
            **FOCUS AREA DETAILS ({focus}):**
            [Specific information related to the focus area]
            
            **PAGE ORGANIZATION:**
            [How content is structured]
            
            Be extremely thorough - extract ALL visible text including small print, captions, and footnotes.
            """
            
            response = self.processor.model.generate_content([analyze_prompt] + pages_to_analyze)
            result = response.text.strip()
            return self._format_response(result, f"Page Analysis ({', '.join(map(str, actual_pages))})")
            
        except Exception as e:
            return f"❌ Error analyzing pages: {str(e)}"
    
    async def get_catalog_overview(self) -> str:
        """Get comprehensive overview of the catalog."""
        try:
            print(f"\n=== CATALOG OVERVIEW ===")
            print(f"Catalog: {self.catalog_name}")
            
            overview_prompt = f"""
            Provide a comprehensive overview of catalog "{self.catalog_name}".
            
            CATALOG SUMMARY:
            {self.catalog_summary}
            
            PRODUCT INDEX:
            {self.product_index[:8000]}
            
            CATALOG DATA SAMPLE:
            {self.catalog_data[:6000]}
            
            CREATE COMPLETE OVERVIEW:
            
            **CATALOG OVERVIEW: {self.catalog_name}**
            
            **Business Information:**
            - Company name and type
            - Business focus and specialization
            - Target market and customer base
            
            **Product Categories:**
            - Main product categories (list all)
            - Number of products in each category
            - Specialty or featured product lines
            
            **Product Range:**
            - Total estimated number of products
            - Price ranges (lowest to highest)
            - Featured or premium products
            - Popular or best-selling items
            
            **Key Brands and Manufacturers:**
            - All brands represented
            - Exclusive or featured brands
            - Private label products
            
            **Catalog Organization:**
            - Total pages: {len(self.pdf_images)}
            - How content is organized
            - Main sections and their purposes
            - Special features (index, guides, etc.)
            
            **Services and Information:**
            - Warranty and support information
            - Ordering and contact details
            - Special services offered
            - Technical support availability
            
            **Sample Products:**
            [List 10-15 representative products with brief details]
            
            **How to Use This Catalog:**
            - Best ways to search for products
            - Key sections to check for specific needs
            - Tips for finding product information
            
            Make this a comprehensive, useful overview that helps users understand what's available.
            """
            
            response = self.processor.model.generate_content(overview_prompt)
            result = response.text.strip()
            return self._format_response(result, "Catalog Overview")
            
        except Exception as e:
            return f"❌ Error generating catalog overview: {str(e)}"