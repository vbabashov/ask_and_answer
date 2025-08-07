"""
Enhanced catalog tools that actually use the full catalog content for searches
This replaces the missing CatalogTools implementation
"""

import re
from typing import List, Dict, Any, Optional
from PIL import Image
from difflib import SequenceMatcher
import json

from processors.pdf_processor import PDFCatalogProcessor

class CatalogTools:
    """Tools for searching and analyzing catalog content using the full extracted data."""
    
    def __init__(self, catalog_data: str, pdf_images: List[Image.Image], 
                 processor: PDFCatalogProcessor, catalog_name: str, 
                 product_index: str, catalog_summary: str):
        self.catalog_data = catalog_data  # Full catalog content
        self.pdf_images = pdf_images
        self.processor = processor
        self.catalog_name = catalog_name
        self.product_index = product_index  # Product index for quick lookup
        self.catalog_summary = catalog_summary
        
        # Create searchable chunks from catalog data
        self.content_chunks = self._create_searchable_chunks()
        
    def _create_searchable_chunks(self) -> List[Dict[str, Any]]:
        """Create searchable chunks from the full catalog content."""
        chunks = []
        
        # Split content by sections/pages
        sections = re.split(r'===\s*(?:PAGES?|SECTION)\s*\d+.*?===', self.catalog_data)
        
        for i, section in enumerate(sections):
            if section.strip():
                chunks.append({
                    'id': f'section_{i}',
                    'content': section.strip(),
                    'page_range': self._extract_page_numbers(section),
                    'products': self._extract_products_from_section(section)
                })
        
        return chunks
    
    def _extract_page_numbers(self, content: str) -> str:
        """Extract page number references from content."""
        page_matches = re.findall(r'(?:page|p\.?)\s*(\d+)', content.lower())
        if page_matches:
            return f"Pages {'-'.join(set(page_matches))}"
        return "Page reference not found"
    
    def _extract_products_from_section(self, content: str) -> List[str]:
        """Extract product names from a content section."""
        # Look for patterns that typically indicate products
        product_patterns = [
            r'(?:^|\n)\s*[-•]\s*([A-Z][^.\n]{10,60})',  # Bullet points with products
            r'(?:Model|Product|Item):\s*([A-Z][^.\n]{5,40})',  # Model/Product labels
            r'\b([A-Z][a-zA-Z0-9\s&-]{5,40})\s*[\$€£]\d+',  # Product names with prices
        ]
        
        products = []
        for pattern in product_patterns:
            matches = re.findall(pattern, content)
            products.extend([match.strip() for match in matches])
        
        return list(set(products))  # Remove duplicates
    
    async def search_products(self, query: str) -> str:
        """Search for products in the catalog using the full content."""
        query_lower = query.lower()
        query_words = re.findall(r'\w+', query_lower)
        
        print(f"🔍 Searching catalog '{self.catalog_name}' for: {query}")
        print(f"Available content chunks: {len(self.content_chunks)}")
        
        # First, search in the product index for quick matches
        index_results = self._search_product_index(query, query_words)
        
        # Then search in the full content
        content_results = self._search_full_content(query, query_words)
        
        # Combine and format results
        combined_results = self._combine_search_results(index_results, content_results, query)
        
        if combined_results:
            return self._format_search_results(combined_results, query)
        else:
            # No results found - provide helpful alternative
            return self._generate_no_results_response(query)
    
    def _search_product_index(self, query: str, query_words: List[str]) -> List[Dict]:
        """Search the product index for quick matches."""
        results = []
        index_lower = self.product_index.lower()
        
        # Look for exact matches first
        if query.lower() in index_lower:
            # Extract relevant sections from the index
            lines = self.product_index.split('\n')
            relevant_lines = []
            
            for line in lines:
                if any(word in line.lower() for word in query_words):
                    relevant_lines.append(line.strip())
            
            if relevant_lines:
                results.append({
                    'source': 'product_index',
                    'content': '\n'.join(relevant_lines),
                    'relevance': 'high',
                    'type': 'index_match'
                })
        
        return results
    
    def _search_full_content(self, query: str, query_words: List[str]) -> List[Dict]:
        """Search the full catalog content for detailed matches."""
        results = []
        
        for chunk in self.content_chunks:
            content_lower = chunk['content'].lower()
            relevance_score = 0
            
            # Calculate relevance based on query word matches
            for word in query_words:
                if len(word) > 2:  # Skip very short words
                    if word in content_lower:
                        relevance_score += 1
                        # Boost score for exact phrase matches
                        if query.lower() in content_lower:
                            relevance_score += 2
            
            # If this chunk has relevant content
            if relevance_score > 0:
                results.append({
                    'source': 'full_content',
                    'content': chunk['content'],
                    'page_range': chunk['page_range'],
                    'products': chunk['products'],
                    'relevance_score': relevance_score,
                    'type': 'content_match'
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:5]  # Top 5 most relevant chunks
    
    def _combine_search_results(self, index_results: List[Dict], content_results: List[Dict], query: str) -> List[Dict]:
        """Combine and deduplicate search results."""
        all_results = []
        
        # Add index results first (they're typically more precise)
        all_results.extend(index_results)
        
        # Add content results
        all_results.extend(content_results)
        
        return all_results
    
    def _format_search_results(self, results: List[Dict], query: str) -> str:
        """Format search results into a readable response."""
        response = f"**Search Results for '{query}' in catalog: {self.catalog_name}**\n\n"
        
        for i, result in enumerate(results, 1):
            if result['type'] == 'index_match':
                response += f"**📋 Product Index Match:**\n"
                response += f"{result['content']}\n\n"
            
            elif result['type'] == 'content_match':
                response += f"**📖 Detailed Information ({result['page_range']}):**\n"
                
                # Extract the most relevant part of the content
                content = result['content']
                if len(content) > 800:  # Truncate very long content
                    # Try to find the most relevant paragraph
                    paragraphs = content.split('\n\n')
                    best_paragraph = ""
                    best_score = 0
                    
                    query_words = re.findall(r'\w+', query.lower())
                    for paragraph in paragraphs:
                        paragraph_lower = paragraph.lower()
                        score = sum(1 for word in query_words if word in paragraph_lower)
                        if score > best_score:
                            best_score = score
                            best_paragraph = paragraph
                    
                    content = best_paragraph if best_paragraph else paragraphs[0]
                
                response += f"{content}\n\n"
                
                # Add extracted products if available
                if result.get('products'):
                    response += f"**🔍 Related Products:** {', '.join(result['products'][:5])}\n\n"
            
            response += "---\n\n"
        
        response += f"*Source: {self.catalog_name} catalog*"
        return response
    
    def _generate_no_results_response(self, query: str) -> str:
        """Generate a helpful response when no results are found."""
        response = f"**No direct matches found for '{query}' in catalog: {self.catalog_name}**\n\n"
        
        # Try to suggest alternatives based on available content
        if self.product_index:
            # Extract some example products from the index
            lines = self.product_index.split('\n')[:10]  # First 10 lines
            example_products = []
            for line in lines:
                if '-' in line or '•' in line:  # Likely product lines
                    clean_line = re.sub(r'^[-•\s]+', '', line).strip()
                    if clean_line and len(clean_line) > 10:
                        example_products.append(clean_line)
            
            if example_products:
                response += f"**Available products in this catalog include:**\n"
                for product in example_products[:5]:
                    response += f"• {product}\n"
                response += "\n"
        
        response += f"**Suggestions:**\n"
        response += f"• Try different keywords or product names\n"
        response += f"• Ask for a category overview (e.g., 'What kitchen appliances do you have?')\n"
        response += f"• Request a general catalog overview\n\n"
        response += f"*Catalog: {self.catalog_name}*"
        
        return response
    
    async def get_product_details(self, product_name: str) -> str:
        """Get detailed information about a specific product."""
        print(f"🔍 Getting details for product: {product_name}")
        
        # Search for the product in full content
        results = await self.search_products(product_name)
        
        if "No direct matches found" not in results:
            return results
        else:
            # Try to analyze specific pages that might contain the product
            return await self._analyze_for_specific_product(product_name)
    
    async def _analyze_for_specific_product(self, product_name: str) -> str:
        """Analyze PDF pages specifically looking for a product."""
        try:
            # Use Gemini to analyze pages looking for the specific product
            analysis_prompt = f"""
            Look through these catalog pages specifically for product: "{product_name}"
            
            Extract ALL information about this product including:
            - Complete product name and model variations
            - Detailed specifications and features
            - Pricing information
            - Availability and ordering details
            - Page numbers where found
            - Any related or similar products
            
            If the exact product isn't found, look for:
            - Similar products in the same category
            - Products with similar names or functions
            - Alternative models or variations
            
            Be very thorough and specific.
            """
            
            # Analyze a subset of images for performance
            sample_images = self.pdf_images[:min(15, len(self.pdf_images))]
            response = self.processor.model.generate_content([analysis_prompt] + sample_images)
            
            result = f"**Detailed Analysis for '{product_name}' in {self.catalog_name}:**\n\n"
            result += response.text
            result += f"\n\n*Analysis based on {len(sample_images)} pages from {self.catalog_name}*"
            
            return result
            
        except Exception as e:
            return f"Error analyzing product '{product_name}': {str(e)}"
    
    async def compare_products(self, products: str) -> str:
        """Compare multiple products."""
        product_list = [p.strip() for p in products.split(',')]
        
        comparison_results = []
        for product in product_list:
            result = await self.get_product_details(product)
            comparison_results.append({
                'product': product,
                'details': result
            })
        
        response = f"**Product Comparison in {self.catalog_name}:**\n\n"
        for item in comparison_results:
            response += f"### {item['product']}\n"
            response += f"{item['details']}\n\n"
        
        return response
    
    async def analyze_specific_pages(self, page_numbers: str) -> str:
        """Analyze specific pages in detail."""
        try:
            # Parse page numbers
            pages = []
            for part in page_numbers.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages.extend(range(start, end + 1))
                else:
                    pages.append(int(part))
            
            # Get the specific pages (convert to 0-based indexing)
            page_images = []
            for page_num in pages:
                if 0 < page_num <= len(self.pdf_images):
                    page_images.append(self.pdf_images[page_num - 1])
            
            if not page_images:
                return f"Invalid page numbers. This catalog has {len(self.pdf_images)} pages."
            
            analysis_prompt = f"""
            Analyze these specific pages from catalog {self.catalog_name}.
            
            Provide detailed information about:
            - All products shown with complete details
            - Specifications and features
            - Pricing information
            - Any special offers or notes
            - Organization and categories
            
            Be comprehensive and include all visible text and product information.
            """
            
            response = self.processor.model.generate_content([analysis_prompt] + page_images)
            
            result = f"**Analysis of Pages {page_numbers} from {self.catalog_name}:**\n\n"
            result += response.text
            
            return result
            
        except Exception as e:
            return f"Error analyzing pages {page_numbers}: {str(e)}"
    
    async def get_catalog_overview(self) -> str:
        """Get comprehensive catalog overview using actual content."""
        overview = f"**📋 Comprehensive Overview of {self.catalog_name}**\n\n"
        
        # Basic info
        overview += f"**📊 Basic Information:**\n"
        overview += f"• Total Pages: {len(self.pdf_images)}\n"
        overview += f"• Content Sections: {len(self.content_chunks)}\n\n"
        
        # Summary (metadata-based)
        overview += f"**📝 Catalog Summary:**\n{self.catalog_summary}\n\n"
        
        # Product index preview
        if self.product_index:
            overview += f"**🔍 Product Index Preview:**\n"
            index_lines = self.product_index.split('\n')[:15]  # First 15 lines
            overview += '\n'.join(index_lines)
            if len(self.product_index.split('\n')) > 15:
                overview += f"\n... and {len(self.product_index.split(r'\n')) - 15} more products."
            overview += "\n\n"
        
        # Content statistics
        if self.content_chunks:
            overview += f"**📈 Content Analysis:**\n"
            total_products = sum(len(chunk.get('products', [])) for chunk in self.content_chunks)
            overview += f"• Identified Products: {total_products}\n"
            overview += f"• Searchable Content Sections: {len(self.content_chunks)}\n\n"
        
        overview += f"**💡 Usage Tips:**\n"
        overview += f"• Search for specific products: 'Show me coffee makers'\n"
        overview += f"• Get product details: 'Tell me about [product name]'\n"
        overview += f"• Compare products: 'Compare [product1], [product2]'\n"
        overview += f"• Analyze pages: 'Show me details from pages 5-10'\n"
        
        return overview