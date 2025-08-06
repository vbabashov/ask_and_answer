# main.py - OpenAI Agent SDK with Gemini for PDF Analysis
import asyncio
import logging
from typing import Dict
from datetime import datetime
from openai import AsyncOpenAI

# Import from packages
from config import Config
from models import PDFMetadata
from repositories import CatalogRepository
from services import GeminiService, CatalogService
from services.openai_agent_service import OpenAIAgentService
import nest_asyncio

# Apply nest_asyncio for Streamlit compatibility
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAICatalogSystemFacade:
    """Main facade for the OpenAI Agent SDK powered catalog system"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Validate configuration (both APIs needed)
        if not config.gemini_api_key:
            raise ValueError("Gemini API key is required for PDF analysis")
        
        if not config.openai_api_key:
            raise ValueError("OpenAI API key is required for Agent SDK")
        
        # Initialize core services
        self.repository = CatalogRepository(config.storage_dir)
        self.gemini_service = GeminiService(config.gemini_api_key)
        self.openai_client = AsyncOpenAI(api_key=config.openai_api_key)
        
        # Initialize catalog service for metadata management
        self.catalog_service = CatalogService(self.repository, self.gemini_service)
        
        # Initialize OpenAI agent service (replaces pure Gemini agents)
        self.agent_service = OpenAIAgentService(
            self.catalog_service, 
            self.gemini_service, 
            self.openai_client
        )
        
        # Load existing catalogs
        self._initialize_existing_catalogs()
        
        logger.info("OpenAI Agent SDK powered catalog system initialized successfully")
    
    def _initialize_existing_catalogs(self):
        """Initialize agent service with existing catalogs"""
        try:
            existing_catalogs = self.repository.load_metadata()
            logger.info(f"Found {len(existing_catalogs)} existing catalogs")
            
            # Initialize each existing catalog in the agent service
            for filename, metadata in existing_catalogs.items():
                if metadata.is_processed and metadata.file_path:
                    logger.info(f"Initializing existing catalog with OpenAI agent: {filename}")
                    # Run async initialization
                    asyncio.create_task(
                        self.agent_service.get_catalog_agent(filename)
                    )
                    
        except Exception as e:
            logger.error(f"Error initializing existing catalogs: {e}")
    
    async def add_catalog(self, pdf_file) -> str:
        """Add a new catalog using OpenAI agents with Gemini PDF analysis"""
        try:
            filename = pdf_file.name
            logger.info(f"Adding catalog with OpenAI Agent SDK system: {filename}")
            
            # Check if already processed
            existing_catalogs = self.repository.load_metadata()
            if filename in existing_catalogs and existing_catalogs[filename].is_processed:
                # Still initialize OpenAI agent if not done
                if filename not in self.agent_service.catalog_agents:
                    await self.agent_service.get_catalog_agent(filename)
                return f"✅ Catalog already processed: {filename}"
            
            # Save PDF file
            file_path = self.repository.save_pdf(pdf_file, filename)
            
            # Create basic metadata for storage
            from utils import pdf_to_images
            images = pdf_to_images(file_path, self.config.dpi)
            
            # Generate enhanced metadata using Gemini (keep this part)
            metadata_dict = self.gemini_service.generate_metadata(images, filename)
            
            # Create comprehensive metadata
            catalog_metadata = PDFMetadata(
                filename=filename,
                file_path=file_path,
                summary=metadata_dict.get("summary", f"OpenAI agent-powered catalog: {filename}"),
                categories=metadata_dict.get("categories", ["general"]),
                keywords=metadata_dict.get("keywords", []),
                product_types=metadata_dict.get("product_types", []),
                brand_names=metadata_dict.get("brand_names", []),
                product_names=metadata_dict.get("product_names", []),
                page_count=len(images),
                processing_date=datetime.now(),
                is_processed=False
            )
            
            # Store metadata
            catalogs = self.repository.load_metadata()
            catalogs[filename] = catalog_metadata
            self.repository.save_metadata(catalogs)
            
            # Initialize OpenAI agent (this does the heavy processing)
            logger.info(f"Initializing OpenAI agent for: {filename}")
            await self.agent_service.get_catalog_agent(filename)
            
            # Update metadata as processed
            catalog_metadata.is_processed = True
            catalog_metadata.summary = "Processed with OpenAI agents - ready for intelligent conversations"
            catalogs[filename] = catalog_metadata
            self.repository.save_metadata(catalogs)
            
            # Refresh catalog service and orchestrator
            self.catalog_service.catalogs = self.repository.load_metadata()
            self.agent_service.refresh_orchestrator()
            
            logger.info(f"Successfully processed catalog with OpenAI agents: {filename}")
            return f"✅ Successfully processed catalog with OpenAI Agent SDK: {filename}"
            
        except Exception as e:
            logger.error(f"Error adding catalog: {str(e)}")
            return f"❌ Error adding catalog: {str(e)}"
    
    async def process_query(self, query: str) -> str:
        """Process a user query using OpenAI agents"""
        try:
            logger.info(f"Processing query with OpenAI Agent SDK system: {query}")
            
            # Check if we have any agents ready
            if self.agent_service.get_agent_count() == 0:
                return "No OpenAI agents available for search. Please upload some PDF catalogs first."
                
            return await self.agent_service.process_query(query)
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return f"❌ Error processing query: {str(e)}"
    
    def get_catalog_overview(self) -> str:
        """Get overview of all catalogs with OpenAI agent status"""
        catalogs = self.catalog_service.get_all_catalogs()
        
        if not catalogs:
            return "No catalogs available in the library."
        
        overview = f"**📚 OpenAI Agent SDK Catalog Library**\n\n"
        overview += f"Total Catalogs: {len(catalogs)}\n"
        overview += f"Active OpenAI Agents: {self.agent_service.get_agent_count()}\n"
        overview += f"Agent Model: GPT-4o\n"
        overview += f"PDF Analysis: Gemini-2.5-Flash\n\n"
        
        for filename, metadata in catalogs.items():
            overview += f"📄 **{filename}**\n"
            if metadata.is_processed:
                agent_status = "🤖 Active" if filename in self.agent_service.catalog_agents else "⏳ Initializing"
                overview += f"   • ✅ Processed with hybrid system\n"
                overview += f"   • {agent_status} OpenAI Agent (GPT-4o)\n"
                overview += f"   • 🧠 Intelligent conversation ready\n"
                overview += f"   • 🎯 Advanced tool usage enabled\n"
            else:
                overview += f"   • ⏳ Processing with OpenAI agents...\n"
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
            "openai_agents": self.agent_service.get_agent_count(),
            "agent_model": "GPT-4o",
            "pdf_analysis_model": "Gemini-2.5-Flash",
            "system_ready": self.agent_service.get_agent_count() > 0,
            "system_type": "OpenAI Agent SDK + Gemini PDF Analysis"
        }
    
    def get_catalog_count(self) -> int:
        """Get number of loaded catalogs"""
        return len(self.catalog_service.get_all_catalogs())
    
    def get_agent_count(self) -> int:
        """Get number of active OpenAI agents"""
        return self.agent_service.get_agent_count()
    
    def get_summary_count(self) -> int:
        """Get number of processed catalogs"""
        return self.agent_service.get_summary_count()
    
    def refresh_orchestrator(self):
        """Refresh orchestrator with updated catalog info"""
        logger.info("Refreshing OpenAI orchestrator agent")
        self.agent_service.refresh_orchestrator()

# Backward compatibility alias
CatalogSystemFacade = OpenAICatalogSystemFacade

# Main entry point for running the Streamlit app
def main():
    """Main entry point"""
    from ui import create_streamlit_app
    create_streamlit_app()

if __name__ == "__main__":
    main()