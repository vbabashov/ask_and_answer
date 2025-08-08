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
        # FIXED: Simpler extraction prompt
        extraction_prompt = f"""
        Extract all visible text and product information from these catalog pages.
        
        Focus on:
        - Product names and models
        - Specifications and features
        - Prices and part numbers
        - Categories and sections
        
        Format as structured content with product listings.
        """
        
        try:
            response = self.processor.model.generate_content([extraction_prompt] + images)
            if hasattr(response, 'text') and response.text:
                return response.text
            else:
                return f"Content extraction failed for pages {batch_start + 1}-{batch_start + len(images)}"
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

                **MANDATORY BEHAVIOR:**
                1. For ANY product question, ALWAYS use extract_complete_catalog_information first
                2. This tool will re-analyze the entire catalog to extract comprehensive information
                3. NEVER give vague responses - always provide detailed, specific information
                4. Include complete specifications, instructions, and technical details

                **AVAILABLE TOOLS (use in this order):**
                1. extract_complete_catalog_information - Use FIRST for comprehensive analysis
                2. search_products - Use as backup if needed
                3. get_product_details - For specific product focus
                4. analyze_specific_pages - For page-specific analysis

                **RESPONSE REQUIREMENTS:**
                - Always extract complete information from the catalog
                - Include technical specifications, usage instructions, warranty details
                - Provide step-by-step instructions when available
                - Reference specific pages and sections
                - Be comprehensive and detailed

                **CATALOG:** {self.catalog_name}

                Remember: Users want complete information from the catalog, not acknowledgments!
                Always use extract_complete_catalog_information for any product inquiry.
                """,
                tools=[
                    agents.function_tool(self.tools.search_products),
                    agents.function_tool(self.tools.extract_complete_catalog_information),
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
        """Enhanced chat response with text search fallback."""
        if not self.agent:
            print(f"Agent not available for {self.catalog_name}, using text search...")
            if self.tools:
                return await self.tools.search_products(question)
            else:
                return f"❌ Catalog {self.catalog_name} not properly initialized."
            
        try:
            # FIXED: Try text search first for reliability
            if self.tools:
                text_result = self.tools._fallback_text_search(question)
                if len(text_result) > 150 and "No information found" not in text_result:
                    return text_result
            
            # Try agent if text search didn't work well
            print(f"\n=== CATALOG AGENT RESPONSE ===")
            print(f"Catalog: {self.catalog_name}")
            print(f"Question: {question}")
            
            result = await agents.Runner.run(self.agent, input=question)
            
            # Extract response text (existing code remains the same)
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

            if not response_text and hasattr(result, 'final_output'):
                response_text = str(result.final_output)

            # Fallback to text search if agent response is poor
            if (not response_text or len(response_text.strip()) < 50 or 
                "no information" in response_text.lower()):
                if self.tools:
                    return self.tools._fallback_text_search(question)

            return response_text or f"Unable to find information about '{question}' in catalog {self.catalog_name}."
                    
        except Exception as e:
            print(f"Chat response error for {self.catalog_name}: {str(e)}")
            # Use text search as final fallback
            if self.tools:
                return self.tools._fallback_text_search(question)
            return f"Error processing '{question}' in {self.catalog_name}: {str(e)}"