"""
Main system that manages orchestrator and individual catalog agents
"""

from typing import Dict
from openai import AsyncOpenAI

from storage.catalog_library import CatalogLibrary
from custom_agents.orchestrator_agent import OrchestratorAgent
from custom_agents.catalog_agent import PDFCatalogAgent

class MultiCatalogSystem:
    """Main system that manages orchestrator and individual catalog agents."""
    
    def __init__(self, gemini_api_key: str, openai_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.catalog_library = CatalogLibrary()
        self.catalog_library._load_metadata()  # Load existing metadata
        self.orchestrator = OrchestratorAgent(gemini_api_key, self.openai_client, self.catalog_library, self)
        self.catalog_agents: Dict[str, PDFCatalogAgent] = {}
        
    async def add_catalog(self, pdf_file) -> str:
        """Add a new catalog to the system."""
        try:
            # Add to library and get metadata
            metadata = self.catalog_library.add_catalog(pdf_file, self.orchestrator.processor)
            
            # Print debug info about the added catalog
            print(f"\n=== CATALOG ADDED ===")
            print(f"Filename: {metadata.filename}")
            print(f"Summary: {metadata.summary}")
            print(f"Categories: {metadata.categories}")
            print(f"Product Types: {metadata.product_types}")
            print(f"Keywords: {metadata.keywords}")
            
            # Reinitialize orchestrator with updated catalog info
            self.orchestrator._initialize_agent()
            
            return f"✅ Successfully added catalog: {metadata.filename}"
            
        except Exception as e:
            return f"❌ Error adding catalog: {str(e)}"
    
    async def get_catalog_agent(self, catalog_name: str) -> PDFCatalogAgent:
        """Get or create a catalog agent for specific catalog."""
        if catalog_name not in self.catalog_agents:
            if catalog_name not in self.catalog_library.catalogs:
                raise Exception(f"Catalog {catalog_name} not found in library")
            
            print(f"Creating new agent for catalog: {catalog_name}")
            # Create new agent
            agent = PDFCatalogAgent(self.gemini_api_key, self.openai_client, catalog_name)
            catalog_path = self.catalog_library.catalogs[catalog_name].file_path
            
            # Initialize the agent with the catalog
            await agent.initialize_catalog(catalog_path)
            
            # Store the agent
            self.catalog_agents[catalog_name] = agent
        
        return self.catalog_agents[catalog_name]
    
    async def process_query(self, question: str) -> str:
        """Process a user query using the orchestrator agent."""
        try:
            print(f"\n=== SYSTEM QUERY PROCESSING ===")
            print(f"Available catalogs: {list(self.catalog_library.catalogs.keys())}")
            print(f"Question: {question}")
            
            # The orchestrator will now automatically select the best catalog and get the answer
            orchestrator_response, selected_catalog = await self.orchestrator.chat_response(question)
            return orchestrator_response
        except Exception as e:
            print(f"Error in system query processing: {str(e)}")
            return f"❌ Error processing query: {str(e)}"