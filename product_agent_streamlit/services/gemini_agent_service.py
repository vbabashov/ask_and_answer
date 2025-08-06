# services/gemini_agent_service.py
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
import json

from services.catalog_service import CatalogService
from services.gemini_service import GeminiService
from utils import pdf_to_images

logger = logging.getLogger(__name__)

class GeminiCatalogAgentTools:
    """Tools for individual catalog agents using Gemini"""
    
    def __init__(self, catalog_name: str, gemini_service: GeminiService, catalog_data: str):
        self.catalog_name = catalog_name
        self.gemini_service = gemini_service
        self.catalog_data = catalog_data
    
    async def search_products(self, query: str) -> str:
        """Search for products in this specific catalog using Gemini"""
        search_prompt = f"""
        You are an expert product specialist for catalog "{self.catalog_name}".
        
        User Query: "{query}"
        
        Catalog Data:
        {self.catalog_data[:15000]}
        
        TASK: Search thoroughly for products related to "{query}" in this catalog.
        
        Provide detailed information including:
        - Exact product names and model numbers
        - Complete specifications and features
        - Prices and availability
        - Page numbers where found
        - Why each product matches the query
        - Comparison with similar products if multiple matches
        
        If no exact matches found:
        - Clearly state no exact matches
        - Suggest similar or related products
        - List main product categories available
        
        Be thorough, accurate, and helpful. Format as a clear, organized response.
        """
        
        try:
            response = self.gemini_service.model.generate_content(search_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error in product search: {e}")
            return f"Error searching products in {self.catalog_name}: {e}"
    
    async def get_product_details(self, product_name: str) -> str:
        """Get detailed information about a specific product using Gemini"""
        detail_prompt = f"""
        You are a product specialist for catalog "{self.catalog_name}".
        
        User wants detailed information about: "{product_name}"
        
        Catalog Data:
        {self.catalog_data[:15000]}
        
        TASK: Provide comprehensive details about "{product_name}" including:
        - Complete technical specifications
        - All available features and capabilities
        - Pricing information and variations
        - Dimensions, weight, materials
        - Installation or setup requirements
        - Warranty and support information
        - Page references
        - Compatible accessories or related products
        
        If the exact product isn't found, look for similar products and explain the differences.
        Be extremely detailed and technical where appropriate.
        """
        
        try:
            response = self.gemini_service.model.generate_content(detail_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return f"Error getting details for {product_name}: {e}"
    
    async def compare_products(self, product1: str, product2: str) -> str:
        """Compare two products using Gemini"""
        comparison_prompt = f"""
        You are a product comparison expert for catalog "{self.catalog_name}".
        
        Compare these products: "{product1}" vs "{product2}"
        
        Catalog Data:
        {self.catalog_data[:15000]}
        
        TASK: Provide a detailed side-by-side comparison including:
        - Specifications comparison table
        - Feature differences and similarities
        - Price comparison
        - Performance differences
        - Use case recommendations
        - Pros and cons of each
        - Which product is better for specific needs
        
        If either product isn't found, suggest the closest alternatives.
        Format as a clear, organized comparison.
        """
        
        try:
            response = self.gemini_service.model.generate_content(comparison_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error comparing products: {e}")
            return f"Error comparing {product1} and {product2}: {e}"
    
    async def analyze_specific_pages(self, page_numbers: str) -> str:
        """Analyze specific pages using Gemini"""
        page_prompt = f"""
        You are analyzing specific pages from catalog "{self.catalog_name}".
        
        User wants information from pages: {page_numbers}
        
        Catalog Data:
        {self.catalog_data[:15000]}
        
        TASK: Extract and summarize all relevant information from pages {page_numbers}:
        - All products mentioned on these pages
        - Complete product details and specifications
        - Pricing and availability information
        - Any special offers or promotions
        - Technical diagrams or important notes
        
        Organize the information clearly by page number.
        """
        
        try:
            response = self.gemini_service.model.generate_content(page_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error analyzing pages: {e}")
            return f"Error analyzing pages {page_numbers}: {e}"
    
    async def get_catalog_overview(self) -> str:
        """Get overview of this catalog using Gemini"""
        overview_prompt = f"""
        Provide a comprehensive overview of catalog "{self.catalog_name}".
        
        Catalog Data:
        {self.catalog_data[:10000]}
        
        TASK: Create a detailed catalog overview including:
        - Main product categories and types
        - Featured products and bestsellers
        - Price ranges for different categories
        - Special features or unique offerings
        - Target customers or markets
        - Company information and contact details
        - Total number of products/pages
        
        Format as an organized, informative overview.
        """
        
        try:
            response = self.gemini_service.model.generate_content(overview_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error getting catalog overview: {e}")
            return f"Error getting overview for {self.catalog_name}: {e}"

class GeminiCatalogAgent:
    """Gemini-powered catalog agent that simulates OpenAI agent functionality"""
    
    def __init__(self, catalog_name: str, gemini_service: GeminiService):
        self.catalog_name = catalog_name
        self.gemini_service = gemini_service
        self.catalog_data = ""
        self.tools = None
        self.is_initialized = False
    
    async def initialize(self, pdf_path: str) -> None:
        """Initialize catalog agent with PDF data using Gemini"""
        if self.is_initialized:
            return
            
        logger.info(f"Initializing Gemini catalog agent: {self.catalog_name}")
        
        # Convert PDF to images and analyze
        images = pdf_to_images(pdf_path)
        
        # Analyze catalog in batches using Gemini
        batch_size = 10
        all_analyses = []
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            analysis = self.gemini_service.analyze_catalog_batch(batch, i)
            all_analyses.append(f"=== PAGES {i+1}-{min(i+batch_size, len(images))} ===\n{analysis}")
        
        # Consolidate analyses
        full_analysis = "\n\n".join(all_analyses)
        self.catalog_data = self.gemini_service.consolidate_catalog_content(full_analysis, self.catalog_name)
        
        # Create tools
        self.tools = GeminiCatalogAgentTools(self.catalog_name, self.gemini_service, self.catalog_data)
        
        self.is_initialized = True
        logger.info(f"✅ Gemini Catalog agent initialized: {self.catalog_name}")
    
    async def chat_response(self, question: str) -> str:
        """Get intelligent chat response using Gemini agent simulation"""
        if not self.is_initialized:
            return f"❌ Catalog {self.catalog_name} not initialized."
        
        try:
            logger.info(f"Gemini Agent processing query: {question} in {self.catalog_name}")
            
            # Simulate agent decision-making using Gemini
            agent_prompt = f"""
            You are an intelligent catalog assistant agent for "{self.catalog_name}".
            
            User Question: "{question}"
            
            Available Tools:
            1. search_products - Search for products by name, category, features, or price
            2. get_product_details - Get detailed information about specific products
            3. compare_products - Compare two products side by side
            4. analyze_specific_pages - Analyze specific pages mentioned by user
            5. get_catalog_overview - Get overview of the entire catalog
            
            AGENT DECISION PROCESS:
            1. Analyze the user's question to determine intent
            2. Decide which tool(s) would best answer the question
            3. Execute the appropriate tool and provide a comprehensive response
            
            For the question "{question}", determine the best approach and provide a helpful response.
            
            If the question is about:
            - Finding products → Use search_products
            - Specific product details → Use get_product_details  
            - Comparing items → Use compare_products
            - Specific pages → Use analyze_specific_pages
            - General overview → Use get_catalog_overview
            
            Provide a natural, conversational response that directly answers the user's question.
            Always mention you are the specialized agent for "{self.catalog_name}".
            """
            
            # First, let Gemini decide the approach
            decision_response = self.gemini_service.model.generate_content(agent_prompt)
            decision = decision_response.text
            
            # Based on the question type, use the appropriate tool
            if any(word in question.lower() for word in ['compare', 'difference', 'vs', 'versus']):
                # Try to extract two products for comparison
                products = self._extract_products_for_comparison(question)
                if len(products) >= 2:
                    tool_response = await self.tools.compare_products(products[0], products[1])
                else:
                    tool_response = await self.tools.search_products(question)
            elif any(word in question.lower() for word in ['page', 'pages']):
                # Extract page numbers if mentioned
                pages = self._extract_page_numbers(question)
                if pages:
                    tool_response = await self.tools.analyze_specific_pages(pages)
                else:
                    tool_response = await self.tools.search_products(question)
            elif any(word in question.lower() for word in ['overview', 'summary', 'catalog', 'all products']):
                tool_response = await self.tools.get_catalog_overview()
            elif any(word in question.lower() for word in ['details', 'specifications', 'specs', 'features']):
                # Extract product name for detailed query
                product_name = self._extract_main_product(question)
                if product_name:
                    tool_response = await self.tools.get_product_details(product_name)
                else:
                    tool_response = await self.tools.search_products(question)
            else:
                # Default to product search
                tool_response = await self.tools.search_products(question)
            
            # Combine agent reasoning with tool response
            final_prompt = f"""
            You are the specialized catalog agent for "{self.catalog_name}".
            
            User asked: "{question}"
            
            Tool Response: {tool_response}
            
            TASK: Provide a natural, conversational response that:
            1. Directly answers the user's question
            2. Uses the tool response information
            3. Adds helpful context and recommendations
            4. Maintains a friendly, knowledgeable tone
            5. Mentions you are the specialist for this catalog
            
            Make it sound like you're an expert who knows this catalog inside and out.
            """
            
            final_response = self.gemini_service.model.generate_content(final_prompt)
            return final_response.text
            
        except Exception as e:
            logger.error(f"Gemini agent error for {self.catalog_name}: {str(e)}")
            try:
                return await self.tools.search_products(question)
            except Exception as tool_error:
                return f"I encountered an error processing your request in {self.catalog_name}: {str(e)}. Please try rephrasing your question."
    
    def _extract_products_for_comparison(self, question: str) -> List[str]:
        """Extract product names for comparison"""
        # Simple extraction - can be enhanced
        words = question.lower().split()
        products = []
        
        # Look for patterns like "X vs Y" or "X and Y"
        for i, word in enumerate(words):
            if word in ['vs', 'versus', 'and', 'or'] and i > 0 and i < len(words) - 1:
                # Take words before and after
                if i > 0:
                    products.append(words[i-1])
                if i < len(words) - 1:
                    products.append(words[i+1])
        
        return products[:2] if len(products) >= 2 else []
    
    def _extract_page_numbers(self, question: str) -> str:
        """Extract page numbers from question"""
        import re
        # Look for patterns like "page 5", "pages 3-7", etc.
        page_pattern = r'pages?\s+(\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*)'
        matches = re.findall(page_pattern, question.lower())
        return matches[0] if matches else ""
    
    def _extract_main_product(self, question: str) -> str:
        """Extract main product name from question"""
        # Simple extraction - look for key product-related words
        words = question.split()
        # Remove common words
        stop_words = {'what', 'are', 'the', 'details', 'of', 'about', 'specifications', 'specs', 'features'}
        product_words = [word for word in words if word.lower() not in stop_words]
        return ' '.join(product_words) if product_words else ""

class GeminiOrchestratorTools:
    """Tools for the Gemini orchestrator agent"""
    
    def __init__(self, catalog_service: CatalogService, agent_service: 'GeminiAgentService'):
        self.catalog_service = catalog_service
        self.agent_service = agent_service
    
    async def answer_query_with_best_catalog(self, query: str) -> str:
        """Find the best catalog and answer using Gemini orchestration"""
        try:
            logger.info(f"Gemini Orchestrator processing query: {query}")
            
            # Find relevant catalogs using Gemini scoring
            relevant_catalogs = self.catalog_service.search_relevant_catalogs(query, top_k=3)
            logger.info(f"Catalog relevance scores: {[(c.catalog_name, c.relevance_score) for c in relevant_catalogs]}")
            
            if not relevant_catalogs:
                return "No suitable catalog found for your query. Please check available catalogs."
            
            best_catalog = relevant_catalogs[0]
            logger.info(f"Selected best catalog: {best_catalog.catalog_name} (score: {best_catalog.relevance_score})")
            
            # Get Gemini catalog agent
            catalog_agent = await self.agent_service.get_catalog_agent(best_catalog.catalog_name)
            
            # Get detailed response from Gemini agent
            detailed_response = await catalog_agent.chat_response(query)
            
            # Try other catalogs if response is poor
            if self._is_poor_response(detailed_response) and len(relevant_catalogs) > 1:
                for catalog_result in relevant_catalogs[1:]:
                    backup_agent = await self.agent_service.get_catalog_agent(catalog_result.catalog_name)
                    backup_response = await backup_agent.chat_response(query)
                    
                    if not self._is_poor_response(backup_response):
                        best_catalog = catalog_result
                        detailed_response = backup_response
                        break
            
            # Format comprehensive response
            result = f"**🎯 Selected Catalog: {best_catalog.catalog_name}**\n"
            result += f"**📊 Relevance Score: {best_catalog.relevance_score:.1f}/10**\n"
            result += f"**💡 Selection Reason:** {best_catalog.reason}\n\n"
            result += f"**🤖 Gemini Agent Response:**\n{detailed_response}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Gemini orchestrator query processing: {str(e)}")
            return f"Error processing query: {str(e)}"
    
    async def search_catalogs(self, query: str) -> str:
        """Search and rank all available catalogs using Gemini"""
        relevant_catalogs = self.catalog_service.search_relevant_catalogs(query, top_k=5)
        
        if not relevant_catalogs:
            return "No catalogs found matching your search criteria."
        
        result = f"**Catalog Search Results for: '{query}'**\n\n"
        for i, catalog in enumerate(relevant_catalogs, 1):
            result += f"{i}. **{catalog.catalog_name}** (Score: {catalog.relevance_score:.1f}/10)\n"
            result += f"   Reason: {catalog.reason}\n\n"
        
        return result
    
    async def get_catalog_overview(self) -> str:
        """Get overview of all available catalogs"""
        catalogs = self.catalog_service.get_all_catalogs()
        
        if not catalogs:
            return "No catalogs available in the system."
        
        overview = f"**📚 Gemini Agent-Powered Catalog Library**\n\n"
        overview += f"Total Catalogs: {len(catalogs)}\n"
        overview += f"Active Gemini Agents: {len(self.agent_service.catalog_agents)}\n\n"
        
        for filename, metadata in catalogs.items():
            overview += f"📄 **{filename}**\n"
            overview += f"   • {metadata.summary}\n"
            overview += f"   • Categories: {', '.join(metadata.categories)}\n"
            overview += f"   • Product Types: {', '.join(metadata.product_types)}\n"
            overview += f"   • Pages: {metadata.page_count}\n"
            overview += f"   • Gemini Agent: {'✅ Active' if filename in self.agent_service.catalog_agents else '⏳ Initializing'}\n\n"
        
        return overview
    
    def _is_poor_response(self, response: str) -> bool:
        """Check if response indicates no relevant information found"""
        poor_indicators = ["no information", "sorry", "not found", "no products matching", "unable to find"]
        return any(indicator in response.lower() for indicator in poor_indicators)

class GeminiOrchestratorAgent:
    """Gemini-powered orchestrator agent"""
    
    def __init__(self, catalog_service: CatalogService, agent_service: 'GeminiAgentService', gemini_service: GeminiService):
        self.catalog_service = catalog_service
        self.agent_service = agent_service
        self.gemini_service = gemini_service
        self.tools = GeminiOrchestratorTools(catalog_service, agent_service)
    
    async def process_query(self, query: str) -> Tuple[str, Optional[str]]:
        """Process query using Gemini orchestrator simulation"""
        try:
            logger.info(f"Gemini Orchestrator processing: {query}")
            
            # Simulate orchestrator decision-making
            orchestrator_prompt = f"""
            You are an intelligent catalog orchestrator powered by Gemini.
            
            User Query: "{query}"
            
            Available Catalogs Summary:
            {self.catalog_service.get_catalog_summaries()}
            
            ORCHESTRATOR TASKS:
            1. Analyze the user query to understand their intent
            2. Determine which catalog would best answer their question
            3. Route the query to the appropriate specialized catalog agent
            4. Provide comprehensive assistance
            
            For any product-related question, you should use the specialized catalog agents.
            
            Available Actions:
            - answer_query_with_best_catalog: Find most relevant catalog and get detailed answer
            - search_catalogs: Show ranking of all catalogs for this query
            - get_catalog_overview: Show overview of all available catalogs
            
            For the query "{query}", the best action is to find the most relevant catalog and get a detailed answer.
            """
            
            # Let Gemini decide the approach, but default to best catalog
            response = await self.tools.answer_query_with_best_catalog(query)
            return response, None
            
        except Exception as e:
            logger.error(f"Error in Gemini orchestrator: {str(e)}")
            return f"Error processing query with Gemini agent: {str(e)}", None
    
    def refresh_orchestrator(self):
        """Refresh orchestrator - not needed for Gemini version"""
        logger.info("Gemini Orchestrator refresh requested")

class GeminiAgentService:
    """Service for managing Gemini-powered catalog agents"""
    
    def __init__(self, catalog_service: CatalogService, gemini_service: GeminiService):
        self.catalog_service = catalog_service
        self.gemini_service = gemini_service
        self.catalog_agents: Dict[str, GeminiCatalogAgent] = {}
        
        # Create Gemini orchestrator
        self.orchestrator = GeminiOrchestratorAgent(catalog_service, self, gemini_service)
    
    async def get_catalog_agent(self, catalog_name: str) -> GeminiCatalogAgent:
        """Get or create a Gemini catalog agent"""
        if catalog_name not in self.catalog_agents:
            catalog_metadata = self.catalog_service.get_catalog_by_name(catalog_name)
            if not catalog_metadata:
                raise ValueError(f"Catalog {catalog_name} not found")
            
            # Create and initialize Gemini agent
            agent = GeminiCatalogAgent(catalog_name, self.gemini_service)
            await agent.initialize(catalog_metadata.file_path)
            
            self.catalog_agents[catalog_name] = agent
        
        return self.catalog_agents[catalog_name]
    
    async def process_query(self, query: str) -> str:
        """Process query using Gemini orchestrator"""
        response, _ = await self.orchestrator.process_query(query)
        return response
    
    def get_agent_count(self) -> int:
        """Get number of active Gemini agents"""
        return len([agent for agent in self.catalog_agents.values() if agent.is_initialized])
    
    def get_summary_count(self) -> int:
        """Get number of initialized catalogs"""
        return len([agent for agent in self.catalog_agents.values() if agent.is_initialized])
    
    def refresh_orchestrator(self):
        """Refresh orchestrator with updated catalog info"""
        self.orchestrator.refresh_orchestrator()