import asyncio
from typing import Dict, Optional, Tuple
import logging

# Import from other packages
from services.catalog_service import CatalogService
from services.gemini_service import GeminiService
from utils import pdf_to_images

logger = logging.getLogger(__name__)

class CatalogAgent:
    """Individual catalog agent"""
    
    def __init__(self, catalog_name: str, gemini_service: GeminiService):
        self.catalog_name = catalog_name
        self.gemini_service = gemini_service
        self.catalog_data = ""
    
    async def initialize(self, pdf_path: str) -> None:
        """Initialize catalog agent with PDF data"""
        logger.info(f"Initializing catalog agent: {self.catalog_name}")
        
        # Convert PDF to images and analyze
        images = pdf_to_images(pdf_path)
        
        # Analyze catalog in batches
        batch_size = 10
        all_analyses = []
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            analysis = self.gemini_service.analyze_catalog_batch(batch, i)
            all_analyses.append(f"=== PAGES {i+1}-{min(i+batch_size, len(images))} ===\n{analysis}")
        
        # Consolidate analyses
        full_analysis = "\n\n".join(all_analyses)
        self.catalog_data = self.gemini_service.consolidate_catalog_content(full_analysis, self.catalog_name)
        
        logger.info(f"Catalog agent initialized: {self.catalog_name}")
    
    async def search_products(self, query: str) -> str:
        """Search for products in the catalog"""
        return self.gemini_service.search_products(query, self.catalog_data, self.catalog_name)
    
    async def chat_response(self, question: str) -> str:
        """Get chat response from agent"""
        try:
            return await self.search_products(question)
        except Exception as e:
            logger.error(f"Chat response error for {self.catalog_name}: {str(e)}")
            return f"I encountered an error processing your request in {self.catalog_name}: {str(e)}"

class OrchestratorAgent:
    """Orchestrator agent that selects appropriate catalogs"""
    
    def __init__(self, catalog_service: CatalogService, agent_service: 'AgentService'):
        self.catalog_service = catalog_service
        self.agent_service = agent_service
    
    async def process_query(self, query: str) -> Tuple[str, Optional[str]]:
        """Process user query and return response with selected catalog"""
        try:
            logger.info(f"Processing query: {query}")
        
            # Find relevant catalogs
            relevant_catalogs = self.catalog_service.search_relevant_catalogs(query, top_k=3)
            logger.info(f"Catalog scores: {[(c.catalog_name, c.relevance_score) for c in relevant_catalogs]}")
            
            if not relevant_catalogs:
                return "No suitable catalog found for your query.", None
            
            best_catalog = relevant_catalogs[0]
            logger.info(f"Selected catalog: {best_catalog.catalog_name} (score: {best_catalog.relevance_score})")
            
            # Get catalog agent
            catalog_agent = await self.agent_service.get_catalog_agent(best_catalog.catalog_name)
            
            # Get detailed response
            detailed_response = await catalog_agent.chat_response(query)
            
            # Try other catalogs if no good match
            if self._is_poor_response(detailed_response) and len(relevant_catalogs) > 1:
                for catalog_result in relevant_catalogs[1:]:
                    backup_agent = await self.agent_service.get_catalog_agent(catalog_result.catalog_name)
                    backup_response = await backup_agent.chat_response(query)
                    
                    if not self._is_poor_response(backup_response):
                        best_catalog = catalog_result
                        detailed_response = backup_response
                        break
            
            # Format response
            result = f"**Selected Catalog: {best_catalog.catalog_name}** (Relevance: {best_catalog.relevance_score}/10)\n\n"
            result += f"**Answer:**\n{detailed_response}"
            
            return result, best_catalog.catalog_name
            
        except Exception as e:
            logger.error(f"Error in orchestrator: {str(e)}")
            return f"Error processing query: {str(e)}", None
    
    def _is_poor_response(self, response: str) -> bool:
        """Check if response indicates no relevant information found"""
        poor_indicators = ["no information", "sorry", "not found", "no products matching"]
        return any(indicator in response.lower() for indicator in poor_indicators)

class AgentService:
    """Service for managing catalog agents"""
    
    def __init__(self, catalog_service: CatalogService, gemini_service: GeminiService):
        self.catalog_service = catalog_service
        self.gemini_service = gemini_service
        self.catalog_agents: Dict[str, CatalogAgent] = {}
        
        # Create orchestrator
        self.orchestrator = OrchestratorAgent(catalog_service, self)
    
    async def get_catalog_agent(self, catalog_name: str) -> CatalogAgent:
        """Get or create a catalog agent"""
        if catalog_name not in self.catalog_agents:
            catalog_metadata = self.catalog_service.get_catalog_by_name(catalog_name)
            if not catalog_metadata:
                raise ValueError(f"Catalog {catalog_name} not found")
            
            # Create and initialize agent
            agent = CatalogAgent(catalog_name, self.gemini_service)
            await agent.initialize(catalog_metadata.file_path)
            
            self.catalog_agents[catalog_name] = agent
        
        return self.catalog_agents[catalog_name]
    
    async def process_query(self, query: str) -> str:
        """Process query using orchestrator"""
        response, _ = await self.orchestrator.process_query(query)
        return response
    
    def refresh_orchestrator(self):
        """Refresh orchestrator with updated catalog info"""
        # Orchestrator doesn't need refreshing in simplified version
        pass