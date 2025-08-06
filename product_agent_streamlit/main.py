import asyncio
import logging
from typing import Dict

# Import from packages
from config import Config
from models import PDFMetadata
from repositories import CatalogRepository
from services import GeminiService, CatalogService, AgentService
import nest_asyncio

# Apply nest_asyncio for Streamlit compatibility
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CatalogSystemFacade:
    """Main facade for the catalog system"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Validate configuration
        if not config.validate():
            raise ValueError("Invalid configuration: missing API keys")
        
        # Initialize services
        self.repository = CatalogRepository(config.storage_dir)
        self.gemini_service = GeminiService(config.gemini_api_key)
        self.catalog_service = CatalogService(self.repository, self.gemini_service)
        self.agent_service = AgentService(self.catalog_service, self.gemini_service)
        
        logger.info("Catalog system initialized successfully")
    
    async def add_catalog(self, pdf_file) -> str:
        """Add a new catalog to the system"""
        try:
            metadata = self.catalog_service.add_catalog(pdf_file, self.config.dpi)
            self.agent_service.refresh_orchestrator()
            return f"✅ Successfully added catalog: {metadata.filename}"
        except Exception as e:
            logger.error(f"Error adding catalog: {str(e)}")
            return f"❌ Error adding catalog: {str(e)}"
    
    async def process_query(self, query: str) -> str:
        """Process a user query"""
        try:
            return await self.agent_service.process_query(query)
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return f"❌ Error processing query: {str(e)}"
    
    def get_catalog_overview(self) -> str:
        """Get overview of all catalogs"""
        catalogs = self.catalog_service.get_all_catalogs()
        
        if not catalogs:
            return "No catalogs available in the library."
        
        overview = f"**Catalog Library Overview**\n\n"
        overview += f"Total Catalogs: {len(catalogs)}\n\n"
        
        for filename, metadata in catalogs.items():
            overview += f"📄 **{filename}**\n"
            overview += f"   • {metadata.summary}\n"
            overview += f"   • Categories: {', '.join(metadata.categories)}\n"
            overview += f"   • Product Types: {', '.join(metadata.product_types)}\n"
            overview += f"   • Pages: {metadata.page_count}\n\n"
        
        return overview
    
    def get_catalog_count(self) -> int:
        """Get number of loaded catalogs"""
        return len(self.catalog_service.get_all_catalogs())
    
    def get_agent_count(self) -> int:
        """Get number of active agents"""
        return len(self.agent_service.catalog_agents)

# Main entry point for running the Streamlit app
def main():
    """Main entry point"""
    from ui import create_streamlit_app
    create_streamlit_app()

if __name__ == "__main__":
    main()