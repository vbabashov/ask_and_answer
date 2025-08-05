"""Tools for the individual catalog agent."""

from typing import List
from PIL import Image

from processors.pdf_processor import PDFCatalogProcessor
from config import MAX_CONSOLIDATION_LENGTH


class CatalogTools:
    """Tools for the individual catalog agent."""
    
    def __init__(self, catalog_data: str, pdf_images: List[Image.Image], processor: PDFCatalogProcessor, catalog_name: str):
        self.catalog_data = catalog_data
        self.pdf_images = pdf_images
        self.processor = processor
        self.catalog_name = catalog_name
    
    async def search_products(self, query: str) -> str:
        """Search for products in the catalog based on query."""
        try:
            print(f"\n=== CATALOG AGENT SEARCH ===")
            print(f"Catalog: {self.catalog_name}")
            print(f"Query: {query}")
            print(f"Catalog data preview: {self.catalog_data[:500]}...")

            search_prompt = f"""
            Based on this catalog data from {self.catalog_name}, search for products related to "{query}":

            {self.catalog_data[:MAX_CONSOLIDATION_LENGTH]}  # Limit for context window

            Provide:
            1. All matching products with full details
            2. Prices and specifications
            3. Page numbers where found
            4. Why each product matches the search
            5. Alternative suggestions if no exact matches

            Format the response clearly with product names, prices, and key details.
            """

            response = self.processor.model.generate_content(search_prompt)
            return response.text

        except Exception as e:
            return f"Error searching products: {str(e)}"
    
    async def get_product_details(self, product_name: str) -> str:
        """Get detailed information about a specific product."""
        try:
            detail_prompt = f"""
            From catalog {self.catalog_name}, find detailed information about "{product_name}":

            {self.catalog_data[:MAX_CONSOLIDATION_LENGTH]}

            Provide complete details including:
            - Full product name and model
            - All specifications and features
            - Price and pricing options
            - Page location
            - Category/section
            - Related products
            - Availability information

            If exact product not found, suggest closest matches.
            """

            response = self.processor.model.generate_content(detail_prompt)
            return response.text

        except Exception as e:
            return f"Error getting product details: {str(e)}"
    
    async def compare_products(self, product1: str, product2: str) -> str:
        """Compare two products from the catalog."""
        try:
            compare_prompt = f"""
            From catalog {self.catalog_name}, compare "{product1}" and "{product2}":

            {self.catalog_data[:MAX_CONSOLIDATION_LENGTH]}

            Provide:
            1. Side-by-side comparison table
            2. Price comparison
            3. Feature differences
            4. Pros and cons for each
            5. Recommendations for different use cases
            6. Page references

            If products not found, suggest similar alternatives.
            """

            response = self.processor.model.generate_content(compare_prompt)
            return response.text

        except Exception as e:
            return f"Error comparing products: {str(e)}"
    
    async def analyze_specific_pages(self, page_numbers: str, focus: str = "general analysis") -> str:
        """Analyze specific pages with focused attention."""
        try:
            pages = [int(p.strip()) for p in page_numbers.split(',') if p.strip().isdigit()]
            valid_pages = [i-1 for i in pages if 0 < i <= len(self.pdf_images)]
            
            if not valid_pages:
                return "No valid page numbers provided. Please specify page numbers separated by commas."
            
            pages_to_analyze = [self.pdf_images[i] for i in valid_pages]
            
            analyze_prompt = f"""
            Analyze pages {page_numbers} from catalog {self.catalog_name} with focus on: {focus}

            Extract:
            1. All products on these pages
            2. Complete text content
            3. Pricing and specifications
            4. Special offers or promotions
            5. Technical details
            6. Contact/ordering information

            Focus area: {focus}
            Be thorough and extract all visible text.
            """

            response = self.processor.model.generate_content([analyze_prompt] + pages_to_analyze)
            return response.text

        except Exception as e:
            return f"Error analyzing pages: {str(e)}"
    
    async def get_catalog_overview(self) -> str:
        """Get an overview of the catalog."""
        try:
            overview_prompt = f"""
            Provide a comprehensive overview of catalog {self.catalog_name}:

            {self.catalog_data[:MAX_CONSOLIDATION_LENGTH]}

            Include:
            1. Business type and product categories
            2. Total number of products
            3. Price ranges
            4. Main sections/categories  
            5. Special features or highlights
            6. Contact and ordering information

            Keep it informative but concise.
            """

            response = self.processor.model.generate_content(overview_prompt)
            return response.text

        except Exception as e:
            return f"Error generating overview: {str(e)}"