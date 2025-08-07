"""
Enhanced individual catalog agent with better product search and initialization
Key improvements:
1. Better catalog content analysis and storage
2. Improved product search with exact matching
3. Enhanced agent instructions for better responses
4. Better error handling and fallbacks
"""

from typing import List
import agents
from PIL import Image
from openai import AsyncOpenAI

from config.settings import AGENT_LLM_NAME
from processors.pdf_processor import PDFCatalogProcessor
from tools.catalog_tools import CatalogTools

class PDFCatalogAgent:
    """Enhanced individual catalog agent."""
    
    def __init__(self, gemini_api_key: str, openai_client: AsyncOpenAI, catalog_name: str):
        self.processor = PDFCatalogProcessor(gemini_api_key)
        self.openai_client = openai_client
        self.catalog_name = catalog_name
        self.catalog_data = ""
        self.catalog_summary = ""
        self.product_index = ""
        self.pdf_images = []
        self.tools = None
        self.agent = None
        
    async def initialize_catalog(self, pdf_path: str) -> None:
        """Enhanced catalog initialization with better content analysis."""
        try:
            print(f"🔄 Initializing catalog agent for: {self.catalog_name}...")
            
            # Convert PDF to images
            self.pdf_images = self.processor.pdf_to_images(pdf_path)
            print(f"✅ Converted {len(self.pdf_images)} pages to images")
            
            # Analyze catalog in smaller, focused batches
            print("🔄 Analyzing catalog content in detail...")
            batch_size = 8  # Smaller batches for better analysis
            all_analyses = []
            
            for i in range(0, len(self.pdf_images), batch_size):
                batch = self.pdf_images[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(self.pdf_images) + batch_size - 1) // batch_size
                
                print(f"Analyzing batch {batch_num}/{total_batches} (pages {i+1}-{min(i+batch_size, len(self.pdf_images))})...")
                
                # Enhanced batch analysis with specific focus
                analysis = await self._analyze_batch_enhanced(batch, i)
                all_analyses.append(f"=== PAGES {i+1}-{min(i+batch_size, len(self.pdf_images))} ===\n{analysis}")
            
            # Create comprehensive catalog knowledge base
            print("🔄 Creating comprehensive catalog knowledge base...")
            await self._create_catalog_knowledge_base(all_analyses)
            
            # Initialize tools with enhanced data
            self.tools = CatalogTools(
                self.catalog_data, 
                self.pdf_images, 
                self.processor, 
                self.catalog_name,
                self.product_index,
                self.catalog_summary
            )
            
            # Create enhanced OpenAI Agent
            await self._initialize_agent()
            
            print(f"✅ Catalog agent for {self.catalog_name} fully initialized!")
            print(f"   - {len(self.pdf_images)} pages processed")
            # Fix the f-string backslash issue
            newline_char = '\n'
            product_count = len(self.product_index.split(newline_char))
            print(f"   - {product_count} products indexed")
            print(f"   - Knowledge base size: {len(self.catalog_data)} characters")
            
        except Exception as e:
            raise Exception(f"Error initializing catalog {self.catalog_name}: {str(e)}")
    
    async def _analyze_batch_enhanced(self, images: List[Image.Image], batch_start: int) -> str:
        """Enhanced batch analysis with focused product extraction."""
        analysis_prompt = f"""
        Analyze pages {batch_start + 1} to {batch_start + len(images)} of catalog "{self.catalog_name}".
        
        EXTRACTION PRIORITIES (in order of importance):
        
        1. **PRODUCTS** (HIGHEST PRIORITY):
           - Extract EVERY product name, including variations and models
           - Record exact product titles as they appear
           - Note all SKUs, model numbers, part numbers
           - Include product descriptions and key features
           - Record ALL pricing information (regular, sale, bulk, etc.)
        
        2. **SPECIFICATIONS**:
           - Technical specifications for each product
           - Dimensions, weights, capacities
           - Performance metrics and ratings
           - Compatibility information
        
        3. **ORGANIZATION**:
           - Section headers and category names
           - Page organization and layout structure
           - Cross-references and related products
        
        4. **ADDITIONAL INFO**:
           - Warranty information
           - Installation/usage instructions
           - Contact information for ordering
        
        **CRITICAL REQUIREMENTS:**
        - Extract ALL visible text, including small print
        - Be extremely thorough with product names
        - Include every price you can find
        - Note exact page numbers for reference
        - Use consistent formatting for easy searching
        
        **FORMAT:**
        Start with a detailed product list, then provide comprehensive content.
        Make everything searchable and well-organized.
        """
        
        try:
            response = self.processor.model.generate_content([analysis_prompt] + images)
            return response.text
        except Exception as e:
            return f"Error analyzing pages {batch_start + 1}-{batch_start + len(images)}: {str(e)}"
    
    async def _create_catalog_knowledge_base(self, all_analyses: List[str]) -> None:
        """Create comprehensive, searchable catalog knowledge base."""
        # Fix the f-string backslash issue
        newline_double = '\n\n'
        full_analysis = newline_double.join(all_analyses)
        
        # Create product index
        index_prompt = f"""
        From this catalog analysis, create a comprehensive PRODUCT INDEX:
        
        {full_analysis[:25000]}  # Use more content for better indexing
        
        Create a searchable product index with:
        1. **COMPLETE PRODUCT LIST** - every product found with exact names
        2. **MODEL VARIATIONS** - all variants and configurations
        3. **PRICING INDEX** - all prices found
        4. **CATEGORY ORGANIZATION** - products grouped by type
        5. **CROSS-REFERENCES** - related and similar products
        
        Format as:
        === PRODUCT INDEX FOR {self.catalog_name} ===
        
        **QUICK PRODUCT LIST:**
        - Product Name 1 (Model: XXX, Price: $XXX, Page: XX)
        - Product Name 2 (Model: YYY, Price: $YYY, Page: XX)
        ...
        
        **BY CATEGORY:**
        Category 1:
        - Detailed product entries...
        
        Make this extremely comprehensive and searchable.
        """
        
        print("Creating product index...")
        try:
            index_response = self.processor.model.generate_content(index_prompt)
            self.product_index = index_response.text
        except Exception as e:
            print(f"Error creating product index: {e}")
            self.product_index = "Product index generation failed."
        
        # Create consolidated catalog data
        consolidation_prompt = f"""
        Create a comprehensive, searchable knowledge base for catalog: {self.catalog_name}
        
        Source Analysis:
        {full_analysis[:30000]}  # Use maximum content
        
        **REQUIREMENTS:**
        1. **COMPLETE PRODUCT DATABASE** - Every product with full details
        2. **SEARCHABLE FORMAT** - Easy to find any product or information
        3. **DETAILED SPECIFICATIONS** - All technical details preserved
        4. **PRICING INFORMATION** - All prices and pricing tiers
        5. **CROSS-REFERENCES** - Related products and alternatives
        6. **PAGE REFERENCES** - Where to find each item
        
        **ORGANIZATION:**
        === CATALOG: {self.catalog_name} ===
        
        === EXECUTIVE SUMMARY ===
        [Brief overview of catalog contents and specialization]
        
        === COMPLETE PRODUCT DATABASE ===
        [Every product with full details, organized for easy searching]
        
        === SPECIFICATIONS INDEX ===
        [Technical details organized by product]
        
        === PRICING GUIDE ===
        [All pricing information organized]
        
        **Make this the ultimate searchable reference for this catalog.**
        Remove duplicates but keep ALL unique information.
        """
        
        print("Creating consolidated knowledge base...")
        try:
            consolidated_response = self.processor.model.generate_content(consolidation_prompt)
            self.catalog_data = consolidated_response.text
        except Exception as e:
            print(f"Error creating consolidated data: {e}")
            self.catalog_data = full_analysis  # Use raw analysis as fallback
        
        # Create catalog summary
        summary_prompt = f"""
        Create a concise but comprehensive summary of catalog: {self.catalog_name}
        
        Based on: {self.catalog_data[:5000]}
        
        Include:
        - Main product categories and specializations
        - Number of products and price ranges
        - Key brands and manufacturers
        - Unique features or specializations
        - Target market or customer base
        
        Keep it under 300 words but make it informative.
        """
        
        try:
            summary_response = self.processor.model.generate_content(summary_prompt)
            self.catalog_summary = summary_response.text
        except Exception as e:
            self.catalog_summary = f"Catalog: {self.catalog_name} with {len(self.pdf_images)} pages of products."
    
    async def _initialize_agent(self) -> None:
        """Initialize OpenAI Agent with Gemini model."""
        try:
            # Import the Gemini adapter
            from adapters.gemini_model import GeminiChatModel
            
            # Create Gemini model instance
            gemini_model = GeminiChatModel(
                model_name="gemini-2.5-flash", 
                api_key=self.processor.model._api_key  # Get API key from processor
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
                name=f"Expert Catalog Assistant - {self.catalog_name}",
                instructions=f"""
                You are an expert product specialist with comprehensive knowledge of catalog: {self.catalog_name}
                
                **CATALOG OVERVIEW:**
                {self.catalog_summary}
                
                **YOUR EXPERTISE:**
                You have complete knowledge of every product in this catalog, including:
                - Exact product names, models, and variations
                - Detailed specifications and features
                - Current pricing and availability
                - Page locations for reference
                - Related products and alternatives
                
                **AVAILABLE TOOLS:**
                - search_products: Find products by any criteria (name, category, price, features)
                - get_product_details: Get complete information about specific products
                - compare_products: Side-by-side product comparisons
                - analyze_specific_pages: Examine specific pages in detail
                - get_catalog_overview: Provide catalog summary and organization
                
                **RESPONSE GUIDELINES:**
                1. **ALWAYS search first** - Use search_products for any product-related query
                2. **Be comprehensive** - Provide complete product information including prices, specs, and page references
                3. **Be accurate** - Only provide information that exists in the catalog
                4. **Be helpful** - If exact product not found, suggest similar or related products
                5. **Include details** - Mention catalog name, page numbers, and specific model information
                6. **Price conscious** - Always include pricing information when available
                
                **SEARCH STRATEGY:**
                - Try different search terms if first attempt doesn't find results
                - Look for product variations and similar items
                - Consider alternative names or categories
                - Search by features or specifications if product names don't work
                
                **WHEN NO EXACT MATCH:**
                - Clearly state what was searched for
                - Suggest the closest alternatives available
                - Explain what products ARE available in relevant categories
                - Offer to search by different criteria
                
                You are the definitive expert on catalog: {self.catalog_name}
                Always provide accurate, detailed, and helpful responses.
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