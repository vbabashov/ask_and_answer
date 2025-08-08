"""
Enhanced individual catalog agent with better product search and initialization
Key improvements:
1. Better catalog content analysis and storage
2. Improved product search with actual content usage
3. Enhanced agent instructions for better responses
4. Better error handling and fallbacks
"""

from typing import List
import agents
from PIL import Image
from openai import AsyncOpenAI

from config.settings import AGENT_LLM_NAME
from processors.pdf_processor import PDFCatalogProcessor
from tools.catalog_tools import CatalogTools  # This will use our enhanced implementation

class PDFCatalogAgent:
    """Enhanced individual catalog agent that actually uses full catalog content."""
    
    def __init__(self, gemini_api_key: str, openai_client: AsyncOpenAI, catalog_name: str):
        self.processor = PDFCatalogProcessor(gemini_api_key)
        self.openai_client = openai_client
        self.catalog_name = catalog_name
        self.catalog_data = ""  # Full detailed catalog content
        self.catalog_summary = ""  # Brief summary for metadata
        self.product_index = ""  # Searchable product index
        self.pdf_images = []
        self.tools = None
        self.agent = None
        
    async def initialize_catalog(self, pdf_path: str) -> None:
        """Enhanced catalog initialization with comprehensive content extraction."""
        try:
            print(f"🔄 Initializing catalog agent for: {self.catalog_name}...")
            
            # Convert PDF to images
            self.pdf_images = self.processor.pdf_to_images(pdf_path)
            print(f"✅ Converted {len(self.pdf_images)} pages to images")
            
            # STEP 1: Extract ALL content in smaller, focused batches
            print("🔄 Extracting complete catalog content...")
            batch_size = 6  # Smaller batches for thorough extraction
            all_content_sections = []
            
            for i in range(0, len(self.pdf_images), batch_size):
                batch = self.pdf_images[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(self.pdf_images) + batch_size - 1) // batch_size
                
                print(f"Extracting content from batch {batch_num}/{total_batches} (pages {i+1}-{min(i+batch_size, len(self.pdf_images))})...")
                
                # Deep content extraction focused on completeness
                content = await self._extract_complete_content(batch, i)
                all_content_sections.append(f"=== PAGES {i+1}-{min(i+batch_size, len(self.pdf_images))} ===\n{content}")
            
            # STEP 2: Create comprehensive, searchable catalog database
            print("🔄 Building comprehensive catalog database...")
            self.catalog_data = await self._build_catalog_database(all_content_sections)
            
            # STEP 3: Create searchable product index
            print("🔄 Creating searchable product index...")
            self.product_index = await self._create_product_index(all_content_sections)
            
            # STEP 4: Generate concise summary for metadata
            print("🔄 Generating catalog summary...")
            self.catalog_summary = await self._generate_catalog_summary()
            
            # STEP 5: Initialize tools with comprehensive data
            self.tools = CatalogTools(
                self.catalog_data,      # Full detailed content
                self.pdf_images,        # Original images for deep analysis
                self.processor,         # Gemini processor for additional analysis
                self.catalog_name,      # Catalog identifier
                self.product_index,     # Searchable product index
                self.catalog_summary    # Brief summary
            )
            
            # STEP 6: Create enhanced OpenAI Agent
            await self._initialize_agent()
            
            print(f"✅ Catalog agent for {self.catalog_name} fully initialized!")
            print(f"   - {len(self.pdf_images)} pages processed")
            print(f"   - Catalog database size: {len(self.catalog_data)} characters")
            print(f"   - Product index size: {len(self.product_index)} characters")
            print(f"   - Ready for detailed queries!")
            
        except Exception as e:
            raise Exception(f"Error initializing catalog {self.catalog_name}: {str(e)}")
    
    async def _extract_complete_content(self, images: List[Image.Image], batch_start: int) -> str:
        """Extract complete content with focus on thoroughness."""
        extraction_prompt = f"""
        Extract ALL content from pages {batch_start + 1} to {batch_start + len(images)} of catalog "{self.catalog_name}".
        
        **EXTRACTION REQUIREMENTS (Be extremely thorough):**
        
        1. **COMPLETE PRODUCT INVENTORY:**
           - Every product name, including variations, models, SKUs
           - Exact product titles as they appear on pages
           - All model numbers, part numbers, serial numbers
           - Complete product descriptions and features
           - ALL pricing information (regular, sale, bulk, special offers)
           - Product specifications (dimensions, weight, power, etc.)
           - Compatibility and requirements
           - Warranty and support information
        
        2. **COMPREHENSIVE TEXT EXTRACTION:**
           - All visible text including headers, footers, captions
           - Product categories and section headers
           - Technical specifications in detail
           - Installation or usage instructions
           - Company information and contact details
           - Ordering information and codes
           - Even small print and fine text
        
        3. **ORGANIZED FORMAT:**
           - Group information by products/categories
           - Preserve page references and organization
           - Make content easily searchable
           - Use consistent formatting for similar items
        
        **CRITICAL: Extract EVERYTHING visible on these pages. This content will be used to answer specific user questions about products, so completeness is essential.**
        
        Format the output as structured, comprehensive content that captures every detail.
        """
        
        try:
            response = self.processor.model.generate_content([extraction_prompt] + images)
            return response.text
        except Exception as e:
            return f"Error extracting content from pages {batch_start + 1}-{batch_start + len(images)}: {str(e)}"
    
    async def _build_catalog_database(self, content_sections: List[str]) -> str:
        """Build comprehensive, searchable catalog database."""
        all_content = "\n\n".join(content_sections)
        
        database_prompt = f"""
        Create a comprehensive, searchable catalog database for: {self.catalog_name}
        
        Source Content:
        {all_content[:25000]}  # Use substantial content for thorough database building
        
        **DATABASE REQUIREMENTS:**
        
        1. **COMPLETE PRODUCT DATABASE:**
           - Every product with full specifications
           - All pricing information organized
           - Detailed feature descriptions
           - Cross-references between related products
        
        2. **SEARCHABLE ORGANIZATION:**
           - Products grouped by categories
           - Alternative names and synonyms included
           - Keywords and search terms embedded
           - Page references for everything
        
        3. **COMPREHENSIVE STRUCTURE:**
        === CATALOG DATABASE: {self.catalog_name} ===
        
        === PRODUCT CATEGORIES ===
        [Organize all products by category with full details]
        
        === COMPLETE PRODUCT LISTINGS ===
        [Every product with specifications, pricing, features, page numbers]
        
        === TECHNICAL SPECIFICATIONS INDEX ===
        [All technical details organized by product]
        
        === PRICING AND AVAILABILITY ===
        [All pricing information and availability details]
        
        === CROSS-REFERENCE INDEX ===
        [Related products, alternatives, compatible items]
        
        **Make this the definitive, searchable reference for this entire catalog.**
        Include ALL information - nothing should be omitted.
        """
        
        try:
            response = self.processor.model.generate_content(database_prompt)
            return response.text
        except Exception as e:
            print(f"Error building catalog database: {e}")
            return all_content  # Fallback to raw content
    
    async def _create_product_index(self, content_sections: List[str]) -> str:
        """Create a searchable product index for quick lookups."""
        all_content = "\n\n".join(content_sections)
        
        index_prompt = f"""
        Create a comprehensive PRODUCT INDEX for catalog: {self.catalog_name}
        
        Source Content:
        {all_content[:20000]}
        
        **INDEX REQUIREMENTS:**
        
        === PRODUCT INDEX: {self.catalog_name} ===
        
        **ALPHABETICAL PRODUCT LIST:**
        A:
        - Product Name A1 (Model: XXX, Price: $XXX, Page: X, Category: XXX)
        - Product Name A2 (Model: YYY, Price: $YYY, Page: X, Category: XXX)
        
        B:
        - Product Name B1 (Model: ZZZ, Price: $ZZZ, Page: X, Category: XXX)
        
        [Continue for all letters with products]
        
        **CATEGORY INDEX:**
        Category 1:
        - Product 1 (Details...)
        - Product 2 (Details...)
        
        **PRICE INDEX:**
        Under $50:
        - Products list...
        $50-$100:
        - Products list...
        [etc.]
        
        **BRAND INDEX:**
        Brand A:
        - Products from this brand...
        
        Make this index comprehensive and easily searchable.
        Include every product found with key details for quick reference.
        """
        
        try:
            response = self.processor.model.generate_content(index_prompt)
            return response.text
        except Exception as e:
            print(f"Error creating product index: {e}")
            return "Product index generation failed - using content search instead."
    
    async def _generate_catalog_summary(self) -> str:
        """Generate concise catalog summary for metadata purposes."""
        summary_prompt = f"""
        Create a concise summary of catalog: {self.catalog_name}
        
        Based on the comprehensive database created, provide:
        - Main product categories and specializations
        - Approximate number of products and price ranges  
        - Key brands and manufacturers represented
        - Target market or customer focus
        - Unique features or specializations of this catalog
        
        Keep it under 200 words but informative for catalog selection purposes.
        
        Database preview: {self.catalog_data[:3000]}
        """
        
        try:
            response = self.processor.model.generate_content(summary_prompt)
            return response.text
        except Exception as e:
            return f"Catalog: {self.catalog_name} containing {len(self.pdf_images)} pages of product information."
    
    async def _initialize_agent(self) -> None:
        """Initialize OpenAI Agent with Gemini model and comprehensive instructions."""
        try:
            # Import the Gemini adapter
            from adapters.gemini_model import GeminiChatModel
            
            # Create Gemini model instance
            gemini_model = GeminiChatModel(
                model_name="gemini-2.5-flash", 
                api_key=self.processor.gemini_api_key
            )
            
            # Create a custom model wrapper for agents SDK
            class GeminiModelWrapper:
                def __init__(self, gemini_client):
                    self.gemini_client = gemini_client
                    
                @property
                def chat(self):
                    return self
                    
                @property
                def completions(self):
                    return self.gemini_client
            
            self.agent = agents.Agent(
                name=f"Expert Catalog Specialist - {self.catalog_name}",
                instructions=f"""
                You are an expert product specialist with COMPLETE access to catalog: {self.catalog_name}
                
                **YOUR COMPREHENSIVE KNOWLEDGE:**
                You have full access to the complete catalog content through your tools:
                - Complete product database with every item, specification, and price
                - Detailed product index for quick lookups
                - Full catalog content for in-depth searches
                - Original catalog pages for visual analysis when needed
                
                **CATALOG SUMMARY (for context only):**
                {self.catalog_summary}
                
                **AVAILABLE TOOLS:**
                - search_products: Search the complete catalog content for any products/information
                - get_product_details: Get comprehensive details about specific products
                - compare_products: Compare multiple products with full specifications
                - analyze_specific_pages: Deep analysis of specific catalog pages
                - get_catalog_overview: Provide complete catalog overview
                
                **RESPONSE STRATEGY:**
                1. **ALWAYS use tools first** - Never guess or use only the summary
                2. **Search comprehensively** - Use search_products for ANY product question
                3. **Be thorough** - Provide complete information including prices, specs, page references
                4. **Use actual content** - Base all answers on the full catalog content, not just summaries
                5. **Multiple searches** - Try different search terms if first attempt needs more information
                
                **QUALITY STANDARDS:**
                - Include specific prices, model numbers, and specifications from the actual catalog
                - Reference exact page numbers where information is found
                - Provide comprehensive product details, not just basic descriptions
                - If exact product not found, search for similar products and explain the differences
                - Always use the complete catalog database through tools - never rely only on summary
                
                **SEARCH STRATEGY:**
                - Primary search with exact query terms
                - Secondary search with broader/related terms if needed
                - Category-based search if product-specific search yields limited results
                - Always get complete product details for any products found
                
                You have complete access to the full catalog content - use it to provide comprehensive, accurate answers.
                """,
                tools=[
                    agents.function_tool(self.tools.search_products),
                    agents.function_tool(self.tools.get_product_details),
                    agents.function_tool(self.tools.compare_products),
                    agents.function_tool(self.tools.analyze_specific_pages),
                    agents.function_tool(self.tools.get_catalog_overview),
                ],
                model=agents.OpenAIChatCompletionsModel(
                    model="gemini",  # Placeholder name
                    openai_client=GeminiModelWrapper(gemini_model)
                ),
            )
            print(f"✅ Enhanced agent initialized for catalog: {self.catalog_name} with Gemini")
        except Exception as e:
            print(f"❌ Error initializing agent for {self.catalog_name}: {e}")
            import traceback
            traceback.print_exc()
            self.agent = None
        
    async def chat_response(self, question: str) -> str:
        """Enhanced chat response with better error handling."""
        if not self.agent:
            print(f"Agent not available for {self.catalog_name}, using direct search...")
            if self.tools:
                return await self.tools.search_products(question)
            else:
                return f"❌ Catalog {self.catalog_name} not properly initialized."
            
        try:
            print(f"\n=== ENHANCED CATALOG AGENT RESPONSE ===")
            print(f"Catalog: {self.catalog_name}")
            print(f"Question: {question}")
            print(f"Available data size: {len(self.catalog_data)} characters")
            
            result = await agents.Runner.run(self.agent, input=question)
            
            # Enhanced response extraction
            response_text = ""
            if hasattr(result, 'messages') and result.messages:
                for message in reversed(result.messages):
                    if hasattr(message, 'role') and message.role == 'assistant':
                        if hasattr(message, 'content'):
                            if isinstance(message.content, str) and message.content.strip():
                                response_text = message.content
                                break
                            elif isinstance(message.content, list):
                                text_parts = []
                                for content_block in message.content:
                                    if hasattr(content_block, 'text') and content_block.text.strip():
                                        text_parts.append(content_block.text)
                                if text_parts:
                                    response_text = ' '.join(text_parts)
                                    break

            # Try final_output if available
            if not response_text and hasattr(result, 'final_output'):
                response_text = str(result.final_output)

            # Enhanced validation - if response seems poor, try direct search
            if response_text and (len(response_text.strip()) < 50 or 
                                "no information" in response_text.lower() or
                                "cannot find" in response_text.lower()):
                print("Agent response seems insufficient, trying direct tool search...")
                direct_response = await self.tools.search_products(question)
                if len(direct_response) > len(response_text):
                    response_text = direct_response

            return response_text or f"Unable to find information about '{question}' in catalog {self.catalog_name}."
                    
        except Exception as e:
            print(f"Enhanced chat response error for {self.catalog_name}: {str(e)}")
            # Enhanced fallback
            try:
                if self.tools:
                    print("Using direct tool fallback...")
                    return await self.tools.search_products(question)
                else:
                    return f"I encountered an error processing your request in {self.catalog_name}. The catalog may need to be reinitialized."
            except Exception as tool_error:
                return f"Error processing '{question}' in {self.catalog_name}: {str(e)}. Please try a different query or contact support."