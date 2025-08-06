# services/openai_agent_service.py
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
import json
from openai import AsyncOpenAI
import agents

from services.catalog_service import CatalogService
from services.gemini_service import GeminiService
from utils import pdf_to_images

logger = logging.getLogger(__name__)

# Use OpenAI model instead of Gemini for agents
AGENT_LLM_NAME = "gemini-2.5-flash"

class OpenAICatalogAgentTools:
    """Tools for individual catalog agents using OpenAI Agent SDK"""
    
    def __init__(self, catalog_name: str, catalog_data: str):
        self.catalog_name = catalog_name
        self.catalog_data = catalog_data
    
    async def search_products(self, query: str) -> str:
        """Search for products in this specific catalog"""
        # This will be handled by the OpenAI agent's function calling
        # The actual search logic will be in the agent's tool function
        pass
    
    async def get_product_details(self, product_name: str) -> str:
        """Get detailed information about a specific product"""
        pass
    
    async def compare_products(self, product1: str, product2: str) -> str:
        """Compare two products"""
        pass
    
    async def analyze_specific_pages(self, page_numbers: str) -> str:
        """Analyze specific pages"""
        pass
    
    async def get_catalog_overview(self) -> str:
        """Get overview of this catalog"""
        pass

class OpenAICatalogAgent:
    """OpenAI Agent SDK powered catalog agent"""
    
    def __init__(self, catalog_name: str, openai_client: AsyncOpenAI, gemini_service: GeminiService):
        self.catalog_name = catalog_name
        self.openai_client = openai_client
        self.gemini_service = gemini_service
        self.catalog_data = ""
        self.agent = None
        self.is_initialized = False
    
    async def initialize(self, pdf_path: str) -> None:
        """Initialize catalog agent with PDF data"""
        if self.is_initialized:
            return
            
        logger.info(f"Initializing OpenAI catalog agent: {self.catalog_name}")
        
        # Use Gemini for PDF analysis (keep this part)
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
        
        # Create OpenAI agent with tools
        self.agent = agents.Agent(
            name=f"Catalog Agent - {self.catalog_name}",
            instructions=f"""
            You are a specialized product catalog agent for "{self.catalog_name}".
            
            You have access to comprehensive product data from this catalog:
            {self.catalog_data[:8000]}  # Truncate for token limits
            
            Your job is to help users find products, compare items, and provide detailed information.
            
            Available tools:
            - search_products: Find products matching user queries
            - get_product_details: Get detailed specs and information
            - compare_products: Compare two or more products
            - analyze_pages: Analyze specific catalog pages
            - get_catalog_overview: Provide catalog summary
            
            Always:
            - Be knowledgeable about products in this catalog
            - Provide accurate pricing and specifications
            - Include page references when available
            - Be helpful and conversational
            - Use tools to provide comprehensive answers
            """,
            tools=[
                agents.function_tool(self._search_products_tool),
                agents.function_tool(self._get_product_details_tool),
                agents.function_tool(self._compare_products_tool),
                agents.function_tool(self._analyze_pages_tool),
                agents.function_tool(self._get_catalog_overview_tool),
            ],
            model=agents.OpenAIChatCompletionsModel(
                model=AGENT_LLM_NAME,
                openai_client=self.openai_client
            ),
        )
        
        self.is_initialized = True
        logger.info(f"✅ OpenAI Catalog agent initialized: {self.catalog_name}")
    
    # Tool functions for OpenAI Agent SDK
    def _search_products_tool(self, query: str) -> str:
        """Search for products in this catalog"""
        search_context = f"""
        Catalog: {self.catalog_name}
        User Query: {query}
        
        Search in this catalog data for products matching "{query}":
        {self.catalog_data[:12000]}
        
        Provide detailed information including:
        - Exact product names and models
        - Complete specifications
        - Prices and availability
        - Page numbers
        - Why each product matches
        """
        
        # Return the context for the agent to process
        return f"Searching catalog '{self.catalog_name}' for '{query}': Found relevant products and details in catalog data."
    
    def _get_product_details_tool(self, product_name: str) -> str:
        """Get detailed product information"""
        return f"Getting detailed information for '{product_name}' from {self.catalog_name} catalog data."
    
    def _compare_products_tool(self, product1: str, product2: str) -> str:
        """Compare two products"""
        return f"Comparing '{product1}' vs '{product2}' using {self.catalog_name} catalog data."
    
    def _analyze_pages_tool(self, page_numbers: str) -> str:
        """Analyze specific pages"""
        return f"Analyzing pages {page_numbers} from {self.catalog_name} catalog."
    
    def _get_catalog_overview_tool(self) -> str:
        """Get catalog overview"""
        return f"Providing overview of {self.catalog_name} catalog with all product categories and highlights."
    
    async def chat_response(self, question: str) -> str:
        """Get response from OpenAI agent"""
        if not self.is_initialized:
            return f"❌ Catalog {self.catalog_name} not initialized."
        
        try:
            logger.info(f"OpenAI Agent processing: {question} in {self.catalog_name}")
            
            # Run the OpenAI agent
            result = await agents.Runner.run(self.agent, input=question)
            
            # Extract response from agent result
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
            
            return response_text or f"No response from {self.catalog_name} agent."
            
        except Exception as e:
            logger.error(f"OpenAI agent error for {self.catalog_name}: {str(e)}")
            return f"I encountered an error processing your request in {self.catalog_name}: {str(e)}"

class OpenAIOrchestratorTools:
    """Tools for the OpenAI orchestrator agent"""
    
    def __init__(self, catalog_service: CatalogService, agent_service: 'OpenAIAgentService'):
        self.catalog_service = catalog_service
        self.agent_service = agent_service
    
    async def answer_query_with_best_catalog(self, query: str) -> str:
        """Find the best catalog and answer using OpenAI orchestration"""
        try:
            logger.info(f"OpenAI Orchestrator processing query: {query}")
            
            # Find relevant catalogs
            relevant_catalogs = self.catalog_service.search_relevant_catalogs(query, top_k=3)
            logger.info(f"Catalog relevance scores: {[(c.catalog_name, c.relevance_score) for c in relevant_catalogs]}")
            
            if not relevant_catalogs:
                return "No suitable catalog found for your query."
            
            best_catalog = relevant_catalogs[0]
            logger.info(f"Selected best catalog: {best_catalog.catalog_name}")
            
            # Get OpenAI catalog agent
            catalog_agent = await self.agent_service.get_catalog_agent(best_catalog.catalog_name)
            
            # Get detailed response
            detailed_response = await catalog_agent.chat_response(query)
            
            # Format comprehensive response
            result = f"**🎯 Selected Catalog: {best_catalog.catalog_name}**\n"
            result += f"**📊 Relevance Score: {best_catalog.relevance_score:.1f}/10**\n"
            result += f"**🤖 OpenAI Agent Response:**\n{detailed_response}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in OpenAI orchestrator: {str(e)}")
            return f"Error processing query: {str(e)}"
    
    def search_catalogs(self, query: str) -> str:
        """Search and rank all available catalogs"""
        relevant_catalogs = self.catalog_service.search_relevant_catalogs(query, top_k=5)
        
        if not relevant_catalogs:
            return "No catalogs found matching your search criteria."
        
        result = f"**Catalog Search Results for: '{query}'**\n\n"
        for i, catalog in enumerate(relevant_catalogs, 1):
            result += f"{i}. **{catalog.catalog_name}** (Score: {catalog.relevance_score:.1f}/10)\n"
            result += f"   Reason: {catalog.reason}\n\n"
        
        return result
    
    def get_catalog_overview(self) -> str:
        """Get overview of all available catalogs"""
        catalogs = self.catalog_service.get_all_catalogs()
        
        if not catalogs:
            return "No catalogs available in the system."
        
        overview = f"**📚 OpenAI Agent-Powered Catalog Library**\n\n"
        overview += f"Total Catalogs: {len(catalogs)}\n"
        overview += f"Active OpenAI Agents: {len(self.agent_service.catalog_agents)}\n\n"
        
        for filename, metadata in catalogs.items():
            overview += f"📄 **{filename}**\n"
            overview += f"   • {metadata.summary}\n"
            overview += f"   • Categories: {', '.join(metadata.categories)}\n"
            overview += f"   • OpenAI Agent: {'✅ Active' if filename in self.agent_service.catalog_agents else '⏳ Initializing'}\n\n"
        
        return overview

class OpenAIOrchestratorAgent:
    """OpenAI Agent SDK powered orchestrator"""
    
    def __init__(self, catalog_service: CatalogService, agent_service: 'OpenAIAgentService', openai_client: AsyncOpenAI):
        self.catalog_service = catalog_service
        self.agent_service = agent_service
        self.openai_client = openai_client
        self.tools = OpenAIOrchestratorTools(catalog_service, agent_service)
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the orchestrator agent"""
        catalog_summary = self.catalog_service.get_catalog_summaries()
        
        self.agent = agents.Agent(
            name="Catalog Orchestrator",
            instructions=f"""
            You are the Catalog Orchestrator Agent powered by OpenAI Agent SDK.
            
            Your job is to answer user questions by selecting the most relevant catalog
            and using that catalog's specialized agent to provide detailed answers.

            Available Catalogs:
            {catalog_summary}

            For ANY product-related question, use the "answer_query_with_best_catalog" tool which will:
            - Find the most relevant catalog based on product types and keywords
            - Get detailed information from that catalog's specialized agent
            - Return a comprehensive answer

            Always be helpful and focus on getting the best possible answer.
            """,
            tools=[
                agents.function_tool(self._answer_query_tool),
                agents.function_tool(self._search_catalogs_tool),
                agents.function_tool(self._get_overview_tool),
            ],
            model=agents.OpenAIChatCompletionsModel(
                model=AGENT_LLM_NAME,
                openai_client=self.openai_client
            ),
        )
    
    def _answer_query_tool(self, query: str) -> str:
        """Tool wrapper for answer_query_with_best_catalog"""
        return asyncio.create_task(self.tools.answer_query_with_best_catalog(query))
    
    def _search_catalogs_tool(self, query: str) -> str:
        """Tool wrapper for search_catalogs"""
        return self.tools.search_catalogs(query)
    
    def _get_overview_tool(self) -> str:
        """Tool wrapper for get_catalog_overview"""
        return self.tools.get_catalog_overview()
    
    async def process_query(self, query: str) -> Tuple[str, Optional[str]]:
        """Process query using OpenAI orchestrator"""
        try:
            logger.info(f"OpenAI Orchestrator processing: {query}")
            
            result = await agents.Runner.run(self.agent, input=query)
            
            # Extract response
            response_text = ""
            if hasattr(result, 'messages') and result.messages:
                for message in reversed(result.messages):
                    if hasattr(message, 'role') and message.role == 'assistant':
                        if hasattr(message, 'content'):
                            if isinstance(message.content, str) and message.content.strip():
                                response_text = message.content
                                break
            
            return response_text or "No response from orchestrator agent.", None
            
        except Exception as e:
            logger.error(f"Error in OpenAI orchestrator: {str(e)}")
            return f"Error processing query: {str(e)}", None

class OpenAIAgentService:
    """Service for managing OpenAI Agent SDK powered catalog agents"""
    
    def __init__(self, catalog_service: CatalogService, gemini_service: GeminiService, openai_client: AsyncOpenAI):
        self.catalog_service = catalog_service
        self.gemini_service = gemini_service
        self.openai_client = openai_client
        self.catalog_agents: Dict[str, OpenAICatalogAgent] = {}
        
        # Create OpenAI orchestrator
        self.orchestrator = OpenAIOrchestratorAgent(catalog_service, self, openai_client)
    
    async def get_catalog_agent(self, catalog_name: str) -> OpenAICatalogAgent:
        """Get or create an OpenAI catalog agent"""
        if catalog_name not in self.catalog_agents:
            catalog_metadata = self.catalog_service.get_catalog_by_name(catalog_name)
            if not catalog_metadata:
                raise ValueError(f"Catalog {catalog_name} not found")
            
            # Create and initialize OpenAI agent
            agent = OpenAICatalogAgent(catalog_name, self.openai_client, self.gemini_service)
            await agent.initialize(catalog_metadata.file_path)
            
            self.catalog_agents[catalog_name] = agent
        
        return self.catalog_agents[catalog_name]
    
    async def process_query(self, query: str) -> str:
        """Process query using OpenAI orchestrator"""
        response, _ = await self.orchestrator.process_query(query)
        return response
    
    def get_agent_count(self) -> int:
        """Get number of active OpenAI agents"""
        return len([agent for agent in self.catalog_agents.values() if agent.is_initialized])
    
    def get_summary_count(self) -> int:
        """Get number of initialized catalogs"""
        return len([agent for agent in self.catalog_agents.values() if agent.is_initialized])
    
    def refresh_orchestrator(self):
        """Refresh orchestrator with updated catalog info"""
        self.orchestrator._initialize_agent()