# multi_catalog_system.py
import os
import tempfile
import asyncio
from typing import Dict, List, Tuple, Optional
from pdf_processor import PDFProcessor
from catalog_manager import CatalogManager
from orchestrator_agent import OrchestratorAgent
from catalog_agent import CatalogAgent
import openai

class MultiCatalogSystem:
    def __init__(self, gemini_api_key: str, openai_api_key: str = None):
        self.gemini_api_key = gemini_api_key
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        # Initialize PDF processor (still using Gemini for PDF processing)
        self.pdf_processor = PDFProcessor(gemini_api_key)
        
        # Initialize OpenAI client for agents first
        if self.openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
        
        # Initialize other components
        self.catalog_manager = CatalogManager()
        self.orchestrator = OrchestratorAgent(gemini_api_key, self.catalog_manager, self.openai_client)
        self.catalog_agents: Dict[str, CatalogAgent] = {}
    
    def add_catalog(self, filename: str, pdf_bytes: bytes) -> bool:
        """Add a new catalog to the system."""
        try:
            # Save PDF temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_bytes)
                tmp_path = tmp_file.name
            
            try:
                # Process PDF using Gemini
                images = self.pdf_processor.pdf_to_images(tmp_path)
                content = self.pdf_processor.extract_full_content(images)
                summary = self.pdf_processor.generate_summary(images, filename)
                
                # Store in catalog manager
                self.catalog_manager.add_catalog(filename, content, summary, len(images))
                
                # Create catalog agent with OpenAI client
                if self.openai_client:
                    self.catalog_agents[filename] = CatalogAgent(
                        filename, content, self.gemini_api_key, self.openai_client
                    )
                else:
                    print(f"Warning: OpenAI client not available, skipping agent creation for {filename}")
                
                return True
            finally:
                os.unlink(tmp_path)  # Clean up temp file
                
        except Exception as e:
            print(f"Error adding catalog {filename}: {e}")
            return False
    
    def search_query(self, query: str) -> Tuple[str, str]:
        """Search for products across catalogs."""
        try:
            # Get best catalog from orchestrator
            try:
                selected_catalog = asyncio.run(self.orchestrator.select_best_catalog(query))
            except Exception as e:
                print(f"Orchestrator error: {e}")
                # Fallback: use first available catalog
                catalogs = list(self.catalog_manager.catalogs.keys())
                selected_catalog = catalogs[0] if catalogs else None
            
            if not selected_catalog:
                return "No relevant catalogs found for your query.", "system"
            
            # Get detailed response from catalog agent
            if selected_catalog in self.catalog_agents:
                agent = self.catalog_agents[selected_catalog]
                
                try:
                    detailed_response = asyncio.run(agent.search_products_sync(query))
                except Exception as e:
                    print(f"Agent error: {e}")
                    # Fallback to simple text search
                    detailed_response = agent._fallback_text_search(query)
                
                response = f"**Selected Catalog: {selected_catalog}**\n\n{detailed_response}"
                return response, selected_catalog
            else:
                return f"Catalog agent for {selected_catalog} not available.", "system"
                
        except Exception as e:
            return f"Error processing query: {str(e)}", "system"
    
    def get_catalog_names(self) -> List[str]:
        """Get list of available catalog names."""
        return list(self.catalog_manager.catalogs.keys())
    
    def get_all_catalog_summaries(self) -> str:
        """Get formatted summaries of all catalogs."""
        return self.catalog_manager.get_all_summaries()