# import asyncio
# import logging
# from typing import Dict
# from datetime import datetime

# # Import from packages
# from config import Config
# from models import PDFMetadata
# from repositories import CatalogRepository
# from services import GeminiService, CatalogService
# from services.improved_agent_service import OptimizedAgentService
# import nest_asyncio

# # Apply nest_asyncio for Streamlit compatibility
# nest_asyncio.apply()

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class CatalogSystemFacade:
#     """Optimized facade that eliminates redundant processing"""
    
#     def __init__(self, config: Config):
#         self.config = config
        
#         # Validate configuration
#         if not config.validate():
#             raise ValueError("Invalid configuration: missing API keys")
        
#         # Initialize core services
#         self.repository = CatalogRepository(config.storage_dir)
#         self.gemini_service = GeminiService(config.gemini_api_key)
        
#         # Initialize catalog service for basic metadata (lightweight)
#         self.catalog_service = CatalogService(self.repository, self.gemini_service)
        
#         # Initialize optimized agent service (single processing)
#         self.agent_service = OptimizedAgentService(self.catalog_service, self.gemini_service)
        
#         # Load existing catalogs efficiently
#         self._initialize_existing_catalogs()
        
#         logger.info("Optimized catalog system initialized successfully")
    
#     def _initialize_existing_catalogs(self):
#         """Initialize existing catalogs without reprocessing"""
#         try:
#             existing_catalogs = self.repository.load_metadata()
#             logger.info(f"Found {len(existing_catalogs)} existing catalogs")
            
#             # Only initialize processed catalogs
#             for filename, metadata in existing_catalogs.items():
#                 if metadata.is_processed and metadata.file_path:
#                     logger.info(f"Loading existing catalog: {filename}")
#                     # Initialize in background to avoid blocking
#                     asyncio.create_task(
#                         self.agent_service.initialize_catalog(filename, metadata.file_path)
#                     )
                    
#         except Exception as e:
#             logger.error(f"Error initializing existing catalogs: {e}")
    
#     async def add_catalog(self, pdf_file) -> str:
#         """Add catalog with single comprehensive processing"""
#         try:
#             filename = pdf_file.name
#             logger.info(f"Adding catalog with optimized single-pass processing: {filename}")
            
#             # Check if already processed
#             existing_catalogs = self.repository.load_metadata()
#             if filename in existing_catalogs and existing_catalogs[filename].is_processed:
#                 # Still need to initialize in agent service if not already done
#                 if filename not in self.agent_service.unified_agents:
#                     await self.agent_service.initialize_catalog(filename, existing_catalogs[filename].file_path)
#                 return f"✅ Catalog already processed: {filename}"
            
#             # Save PDF file
#             file_path = self.repository.save_pdf(pdf_file, filename)
            
#             # Create minimal metadata for storage (no processing yet)
#             from utils import pdf_to_images
#             images = pdf_to_images(file_path, self.config.dpi)
            
#             basic_metadata = PDFMetadata(
#                 filename=filename,
#                 file_path=file_path,
#                 summary="Processing with optimized single-pass system...",
#                 categories=["processing"],
#                 keywords=[],
#                 product_types=[],
#                 brand_names=[],
#                 product_names=[],
#                 page_count=len(images),
#                 processing_date=datetime.now(),
#                 is_processed=False
#             )
            
#             # Store basic metadata
#             catalogs = self.repository.load_metadata()
#             catalogs[filename] = basic_metadata
#             self.repository.save_metadata(catalogs)
            
#             # SINGLE COMPREHENSIVE PROCESSING
#             logger.info(f"Starting single-pass comprehensive processing: {filename}")
#             await self.agent_service.initialize_catalog(filename, file_path)
            
#             # Update metadata as fully processed
#             basic_metadata.is_processed = True
#             basic_metadata.summary = "Processed with optimized single-pass system - ready for intelligent search"
            
#             # Get enhanced metadata from agent if available
#             if filename in self.agent_service.unified_agents:
#                 agent = self.agent_service.unified_agents[filename]
#                 if agent.is_initialized:
#                     summary_data = agent.get_summary_data()
#                     basic_metadata.summary = summary_data.get('detailed_summary', basic_metadata.summary)
#                     basic_metadata.categories = summary_data.get('product_categories', ['general'])
#                     basic_metadata.keywords = summary_data.get('searchable_keywords', [])
#                     basic_metadata.product_types = summary_data.get('product_types', [])
#                     basic_metadata.brand_names = summary_data.get('brands', [])
#                     basic_metadata.product_names = summary_data.get('all_products', [])
            
#             catalogs[filename] = basic_metadata
#             self.repository.save_metadata(catalogs)
            
#             # Refresh catalog service data
#             self.catalog_service.catalogs = self.repository.load_metadata()
            
#             logger.info(f"Successfully processed catalog with single pass: {filename}")
#             return f"✅ Successfully processed catalog with optimized single-pass system: {filename}"
            
#         except Exception as e:
#             logger.error(f"Error adding catalog: {str(e)}")
#             return f"❌ Error adding catalog: {str(e)}"
    
#     async def process_query(self, query: str) -> str:
#         """Process query using optimized system"""
#         try:
#             logger.info(f"Processing query with optimized system: {query}")
            
#             # Check if we have any ready agents
#             if self.agent_service.get_summary_count() == 0:
#                 return "No catalogs available for search. Please upload some PDF catalogs first."
                
#             return await self.agent_service.process_query(query)
#         except Exception as e:
#             logger.error(f"Error processing query: {str(e)}")
#             return f"❌ Error processing query: {str(e)}"
    
#     def get_catalog_overview(self) -> str:
#         """Get overview of all catalogs"""
#         catalogs = self.catalog_service.get_all_catalogs()
        
#         if not catalogs:
#             return "No catalogs available in the library."
        
#         overview = f"**📚 Optimized Catalog Library Overview**\n\n"
#         overview += f"Total Catalogs: {len(catalogs)}\n"
#         overview += f"Ready Agents: {self.agent_service.get_summary_count()}\n"
#         overview += f"Processing Efficiency: Single-Pass ⚡\n\n"
        
#         for filename, metadata in catalogs.items():
#             overview += f"📄 **{filename}**\n"
#             if metadata.is_processed:
#                 overview += f"   • ✅ Optimized single-pass processing complete\n"
#                 overview += f"   • 🚀 Zero redundancy system\n"
#                 overview += f"   • 🎯 Instant search ready\n"
#             else:
#                 overview += f"   • ⏳ Single-pass processing in progress...\n"
#             overview += f"   • Pages: {metadata.page_count}\n"
#             if metadata.processing_date:
#                 overview += f"   • Processed: {metadata.processing_date.strftime('%Y-%m-%d %H:%M')}\n"
#             overview += "\n"
        
#         return overview
    
#     def get_system_status(self) -> Dict[str, any]:
#         """Get detailed system status"""
#         catalogs = self.catalog_service.get_all_catalogs()
#         processed_count = sum(1 for meta in catalogs.values() if meta.is_processed)
        
#         return {
#             "total_catalogs": len(catalogs),
#             "processed_catalogs": processed_count,
#             "summary_agents": self.agent_service.get_summary_count(),
#             "detailed_agents": self.agent_service.get_agent_count(),
#             "ready_agents": self.agent_service.get_summary_count(),
#             "processing_efficiency": "Single-Pass",
#             "system_ready": self.agent_service.get_summary_count() > 0
#         }
    
#     def get_catalog_count(self) -> int:
#         """Get number of loaded catalogs"""
#         return len(self.catalog_service.get_all_catalogs())
    
#     def get_agent_count(self) -> int:
#         """Get number of active agents"""
#         return self.agent_service.get_agent_count()
    
#     def get_summary_count(self) -> int:
#         """Get number of ready catalogs"""
#         return self.agent_service.get_summary_count()
    
#     def refresh_orchestrator(self):
#         """Refresh not needed in optimized system"""
#         logger.info("Orchestrator refresh requested - optimized system auto-manages")
#         pass

# # Main entry point for running the Streamlit app
# def main():
#     """Main entry point"""
#     from ui.streamlit_app import create_streamlit_app
#     create_streamlit_app()

# if __name__ == "__main__":
#     main()
