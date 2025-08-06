# import asyncio
# import logging
# from typing import Dict

# # Import from packages
# from config import Config
# from models import PDFMetadata
# from repositories import CatalogRepository
# from services import GeminiService, CatalogService, AgentService
# import nest_asyncio

# # Apply nest_asyncio for Streamlit compatibility
# nest_asyncio.apply()

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class CatalogSystemFacade:
#     """Main facade for the catalog system"""
    
#     def __init__(self, config: Config):
#         self.config = config
        
#         # Validate configuration
#         if not config.validate():
#             raise ValueError("Invalid configuration: missing API keys")
        
#         # Initialize services
#         self.repository = CatalogRepository(config.storage_dir)
#         self.gemini_service = GeminiService(config.gemini_api_key)
#         self.catalog_service = CatalogService(self.repository, self.gemini_service)
#         self.agent_service = AgentService(self.catalog_service, self.gemini_service)
        
#         logger.info("Catalog system initialized successfully")
    
#     async def add_catalog(self, pdf_file) -> str:
#         """Add a new catalog to the system"""
#         try:
#             metadata = self.catalog_service.add_catalog(pdf_file, self.config.dpi)
#             self.agent_service.refresh_orchestrator()
#             return f"✅ Successfully added catalog: {metadata.filename}"
#         except Exception as e:
#             logger.error(f"Error adding catalog: {str(e)}")
#             return f"❌ Error adding catalog: {str(e)}"
    
#     async def process_query(self, query: str) -> str:
#         """Process a user query"""
#         try:
#             return await self.agent_service.process_query(query)
#         except Exception as e:
#             logger.error(f"Error processing query: {str(e)}")
#             return f"❌ Error processing query: {str(e)}"
    
#     def get_catalog_overview(self) -> str:
#         """Get overview of all catalogs"""
#         catalogs = self.catalog_service.get_all_catalogs()
        
#         if not catalogs:
#             return "No catalogs available in the library."
        
#         overview = f"**Catalog Library Overview**\n\n"
#         overview += f"Total Catalogs: {len(catalogs)}\n\n"
        
#         for filename, metadata in catalogs.items():
#             overview += f"📄 **{filename}**\n"
#             overview += f"   • {metadata.summary}\n"
#             overview += f"   • Categories: {', '.join(metadata.categories)}\n"
#             overview += f"   • Product Types: {', '.join(metadata.product_types)}\n"
#             overview += f"   • Pages: {metadata.page_count}\n\n"
        
#         return overview
    
#     def get_catalog_count(self) -> int:
#         """Get number of loaded catalogs"""
#         return len(self.catalog_service.get_all_catalogs())
    
#     def get_agent_count(self) -> int:
#         """Get number of active agents"""
#         return len(self.agent_service.catalog_agents)

# # Main entry point for running the Streamlit app
# def main():
#     """Main entry point"""
#     from ui import create_streamlit_app
#     create_streamlit_app()

# if __name__ == "__main__":
#     main()

# main.py
import asyncio
import logging
from typing import Dict
from datetime import datetime

# Import from packages
from config import Config
from models import PDFMetadata
from repositories import CatalogRepository
from services import GeminiService, CatalogService
from services.improved_agent_service import ImprovedAgentService
import nest_asyncio

# Apply nest_asyncio for Streamlit compatibility
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CatalogSystemFacade:
    """Main facade for the improved catalog system"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Validate configuration
        if not config.validate():
            raise ValueError("Invalid configuration: missing API keys")
        
        # Initialize core services
        self.repository = CatalogRepository(config.storage_dir)
        self.gemini_service = GeminiService(config.gemini_api_key)
        
        # Initialize catalog service for metadata management
        self.catalog_service = CatalogService(self.repository, self.gemini_service)
        
        # Initialize improved agent service
        self.agent_service = ImprovedAgentService(self.catalog_service, self.gemini_service)
        
        logger.info("Improved catalog system initialized successfully")
    
    async def add_catalog(self, pdf_file) -> str:
        """Add a new catalog using the improved agent system"""
        try:
            filename = pdf_file.name
            logger.info(f"Adding catalog with improved system: {filename}")
            
            # Check if already processed
            existing_catalogs = self.repository.load_metadata()
            if filename in existing_catalogs and existing_catalogs[filename].is_processed:
                return f"✅ Catalog already processed: {filename}"
            
            # Save PDF file
            file_path = self.repository.save_pdf(pdf_file, filename)
            
            # Create basic metadata for storage
            from utils import pdf_to_images
            images = pdf_to_images(file_path, self.config.dpi)
            
            basic_metadata = PDFMetadata(
                filename=filename,
                file_path=file_path,
                summary="Processing with improved agents...",
                categories=["processing"],
                keywords=[],
                product_types=[],
                brand_names=[],
                product_names=[],
                page_count=len(images),
                processing_date=datetime.now(),
                is_processed=False
            )
            
            # Store basic metadata
            catalogs = self.repository.load_metadata()
            catalogs[filename] = basic_metadata
            self.repository.save_metadata(catalogs)
            
            # Initialize with improved agent system (this does the heavy lifting)
            await self.agent_service.initialize_catalog(filename, file_path)
            
            # Update metadata as processed
            basic_metadata.is_processed = True
            basic_metadata.summary = "Processed with improved agent system - ready for intelligent search"
            catalogs[filename] = basic_metadata
            self.repository.save_metadata(catalogs)
            
            # Refresh catalog service data
            self.catalog_service.catalogs = self.repository.load_metadata()
            
            return f"✅ Successfully processed catalog with improved agents: {filename}"
            
        except Exception as e:
            logger.error(f"Error adding catalog: {str(e)}")
            return f"❌ Error adding catalog: {str(e)}"
    
    async def process_query(self, query: str) -> str:
        """Process a user query using improved agents"""
        try:
            logger.info(f"Processing query with improved system: {query}")
            return await self.agent_service.process_query(query)
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return f"❌ Error processing query: {str(e)}"
    
    def get_catalog_overview(self) -> str:
        """Get overview of all catalogs"""
        catalogs = self.catalog_service.get_all_catalogs()
        
        if not catalogs:
            return "No catalogs available in the library."
        
        overview = f"**📚 Improved Catalog Library Overview**\n\n"
        overview += f"Total Catalogs: {len(catalogs)}\n"
        overview += f"Summary Agents: {self.agent_service.get_summary_count()}\n"
        overview += f"Detailed Agents: {self.agent_service.get_agent_count()}\n\n"
        
        for filename, metadata in catalogs.items():
            overview += f"📄 **{filename}**\n"
            if metadata.is_processed:
                overview += f"   • ✅ Processed with improved agents\n"
                overview += f"   • 🤖 Intelligent search ready\n"
                overview += f"   • 🎯 High-accuracy product matching\n"
            else:
                overview += f"   • ⏳ Processing with agents...\n"
            overview += f"   • Pages: {metadata.page_count}\n"
            if metadata.processing_date:
                overview += f"   • Processed: {metadata.processing_date.strftime('%Y-%m-%d %H:%M')}\n"
            overview += "\n"
        
        return overview
    
    def get_system_status(self) -> Dict[str, any]:
        """Get detailed system status"""
        catalogs = self.catalog_service.get_all_catalogs()
        processed_count = sum(1 for meta in catalogs.values() if meta.is_processed)
        
        return {
            "total_catalogs": len(catalogs),
            "processed_catalogs": processed_count,
            "summary_agents": self.agent_service.get_summary_count(),
            "detailed_agents": self.agent_service.get_agent_count(),
            "system_ready": processed_count > 0
        }
    
    def get_catalog_count(self) -> int:
        """Get number of loaded catalogs"""
        return len(self.catalog_service.get_all_catalogs())
    
    def get_agent_count(self) -> int:
        """Get number of active detailed agents"""
        return self.agent_service.get_agent_count()
    
    def get_summary_count(self) -> int:
        """Get number of summary agents"""
        return self.agent_service.get_summary_count()
    
    def refresh_orchestrator(self):
        """Refresh orchestrator (not needed in improved system)"""
        logger.info("Orchestrator refresh requested - improved system handles this automatically")
        pass

# Main entry point for running the Streamlit app
def main():
    """Main entry point"""
    from ui import create_streamlit_app
    create_streamlit_app()

if __name__ == "__main__":
    main()