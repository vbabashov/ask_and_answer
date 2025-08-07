"""
Individual catalog agent for processing specific catalogs
"""

from typing import List
import agents
from PIL import Image
from openai import AsyncOpenAI

from config.settings import AGENT_LLM_NAME
from processors.pdf_processor import PDFCatalogProcessor
from tools.catalog_tools import CatalogTools

class PDFCatalogAgent:
    """Individual catalog agent."""
    
    def __init__(self, gemini_api_key: str, openai_client: AsyncOpenAI, catalog_name: str):
        self.processor = PDFCatalogProcessor(gemini_api_key)
        self.openai_client = openai_client
        self.catalog_name = catalog_name
        self.catalog_data = ""
        self.pdf_images = []
        self.tools = None
        self.agent = None
        
    async def initialize_catalog(self, pdf_path: str) -> None:
        """Initialize catalog by processing PDF."""
        try:
            print(f"🔄 Processing PDF catalog: {self.catalog_name}...")
            
            # Convert PDF to images
            self.pdf_images = self.processor.pdf_to_images(pdf_path)
            print(f"✅ Converted {len(self.pdf_images)} pages to images")
            
            # Analyze catalog in batches
            print("🔄 Analyzing catalog content...")
            batch_size = 10  # Reduced batch size for better analysis
            all_analyses = []
            
            for i in range(0, len(self.pdf_images), batch_size):
                batch = self.pdf_images[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(self.pdf_images) + batch_size - 1) // batch_size
                
                print(f"Analyzing batch {batch_num}/{total_batches} ({len(batch)} pages)...")
                analysis = self.processor.analyze_catalog_batch(batch, i)
                all_analyses.append(f"=== PAGES {i+1}-{min(i+batch_size, len(self.pdf_images))} ===\n{analysis}")
            
            # Combine analyses
            full_analysis = "\n\n".join(all_analyses)
            
            # Create consolidated summary with enhanced product extraction
            consolidation_prompt = f"""
            Create a consolidated, well-organized, and highly searchable knowledge base for catalog {self.catalog_name}.
            
            IMPORTANT REQUIREMENTS:
            1. Extract ALL product names, models, and variations
            2. Create a comprehensive product index at the beginning
            3. Organize by categories and product types
            4. Include ALL specifications, prices, and features
            5. Remove duplicates but keep all unique information
            6. Make it easily searchable for any product query
            
            Original Analysis:
            {full_analysis[:20000]}  # Increased limit for better consolidation
            
            Format as:
            === PRODUCT INDEX ===
            [List all products found with page references]
            
            === DETAILED CATALOG CONTENT ===
            [Organized, searchable content]
            """
            
            print("Creating consolidated catalog knowledge base...")
            consolidated_response = self.processor.model.generate_content(consolidation_prompt)
            self.catalog_data = consolidated_response.text
            
            print(f"Catalog data preview for {self.catalog_name}:")
            print(self.catalog_data[:1000])
            
            # Initialize tools and agent
            self.tools = CatalogTools(self.catalog_data, self.pdf_images, self.processor, self.catalog_name)
            
            # Create OpenAI Agent
            self.agent = agents.Agent(
                name=f"PDF Catalog Assistant - {self.catalog_name}",
                instructions=f"""
                You are an expert product catalog assistant with comprehensive knowledge of the catalog: {self.catalog_name}
                
                You have access to the following tools:
                - search_products: Search for products by name, category, features, or price
                - get_product_details: Get detailed information about specific products
                - compare_products: Compare two products side by side
                - analyze_specific_pages: Analyze specific pages with focused attention
                - get_catalog_overview: Get an overview of the entire catalog
                
                Catalog Overview:
                {self.catalog_data[:3000]}...
                
                Your primary responsibilities:
                1. Answer questions about ANY product in this catalog
                2. Search and recommend products based on customer needs
                3. Provide detailed specifications and pricing
                4. Compare products and make recommendations
                5. Analyze specific pages for detailed information
                6. Help with product selection and purchasing decisions
                
                IMPORTANT GUIDELINES:
                - Always use the search_products tool for any product-related query
                - Be thorough in your searches - check for variations, similar products, and related items
                - If you don't find an exact match, look for similar or related products
                - Always mention the catalog name: {self.catalog_name}
                - Be helpful and accurate, referencing specific page numbers when available
                - If no products match the query, clearly state what products ARE available in this catalog
                
                Be conversational and friendly while providing comprehensive answers.
                """,
                tools=[
                    agents.function_tool(self.tools.search_products),
                    agents.function_tool(self.tools.get_product_details),
                    agents.function_tool(self.tools.compare_products),
                    agents.function_tool(self.tools.analyze_specific_pages),
                    agents.function_tool(self.tools.get_catalog_overview),
                ],
                model=agents.OpenAIChatCompletionsModel(
                    model=AGENT_LLM_NAME, 
                    openai_client=self.openai_client
                ),
            )
            
            print(f"✅ Catalog {self.catalog_name} initialized! {len(self.pdf_images)} pages processed.")
            
        except Exception as e:
            raise Exception(f"Error initializing catalog {self.catalog_name}: {str(e)}")
    
    async def chat_response(self, question: str) -> str:
        """Get chat response using OpenAI Agent SDK."""
        if not self.agent:
            return f"❌ Catalog {self.catalog_name} not initialized."
            
        try:
            print(f"\n=== CATALOG AGENT RESPONSE ===")
            print(f"Catalog: {self.catalog_name}")
            print(f"Question: {question}")
            
            result = await agents.Runner.run(self.agent, input=question)
            print("DEBUG: Agent result:", result)
            
            # Extract the final response
            if hasattr(result, 'messages') and result.messages:
                for message in reversed(result.messages):
                    if hasattr(message, 'role') and message.role == 'assistant':
                        if hasattr(message, 'content'):
                            if isinstance(message.content, str):
                                return message.content
                            elif isinstance(message.content, list):
                                text_parts = []
                                for content_block in message.content:
                                    if hasattr(content_block, 'text'):
                                        text_parts.append(content_block.text)
                                if text_parts:
                                    return ' '.join(text_parts)
            
            # Fallback handling
            print("Using fallback search...")
            return await self.tools.search_products(question)
                    
        except Exception as e:
            print(f"Chat response error for {self.catalog_name}: {str(e)}")
            try:
                return await self.tools.search_products(question)
            except Exception as tool_error:
                return f"I encountered an error processing your request in {self.catalog_name}: {str(e)}. Please try rephrasing your question."