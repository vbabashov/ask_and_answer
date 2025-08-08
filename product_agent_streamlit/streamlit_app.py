# main.py
import streamlit as st
import os
from pathlib import Path
from multi_catalog_system import MultiCatalogSystem

def main():
    st.set_page_config(page_title="Multi-Catalog Search", layout="wide")
    
    st.title("🔍 Multi-Catalog Product Search")
    st.markdown("Upload product catalogs and search across them for detailed product information.")
    
    # Initialize session state
    if 'system' not in st.session_state:
        if not os.getenv('GEMINI_API_KEY'):
            st.error("Please set GEMINI_API_KEY environment variable")
            return
        st.session_state.system = MultiCatalogSystem(os.getenv('GEMINI_API_KEY'))
    
    system = st.session_state.system
    
    # Sidebar for catalog management
    with st.sidebar:
        st.header("📚 Catalog Management")
        
        # Upload catalogs
        uploaded_files = st.file_uploader(
            "Upload Product Catalogs (PDF)",
            type=['pdf'],
            accept_multiple_files=True,
            key="catalog_uploader"
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in system.get_catalog_names():
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        success = system.add_catalog(uploaded_file.name, uploaded_file.read())
                        if success:
                            st.success(f"Added {uploaded_file.name}")
                        else:
                            st.error(f"Failed to add {uploaded_file.name}")
        
        # Show available catalogs
        catalogs = system.get_catalog_names()
        if catalogs:
            st.subheader("Available Catalogs:")
            for catalog in catalogs:
                st.write(f"📄 {catalog}")
    
    # Main search interface
    st.header("🔍 Product Search")
    
    if not system.get_catalog_names():
        st.info("Please upload some PDF catalogs to get started!")
        return
    
    # Search input
    query = st.text_input(
        "What product are you looking for?",
        placeholder="e.g., immersion blender, garage jack, coffee maker",
        key="search_query"
    )
    
    if query:
        with st.spinner("Searching catalogs..."):
            # Get orchestrator response
            response, selected_catalog = system.search_query(query)
            
            # Display results
            if selected_catalog and selected_catalog != "system":
                st.success(f"🎯 Found information in: **{selected_catalog}**")
            
            st.markdown("### Search Results:")
            st.markdown(response)
    
    # Show catalog summaries
    if st.button("Show All Catalog Summaries"):
        summaries = system.get_all_catalog_summaries()
        st.markdown("### Catalog Library Overview:")
        st.markdown(summaries)

if __name__ == "__main__":
    main()

# multi_catalog_system.py
import os
import tempfile
from typing import Dict, List, Tuple, Optional
from pdf_processor import PDFProcessor
from catalog_manager import CatalogManager
from orchestrator_agent import OrchestratorAgent
from catalog_agent import CatalogAgent

class MultiCatalogSystem:
    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.pdf_processor = PDFProcessor(gemini_api_key)
        self.catalog_manager = CatalogManager()
        self.orchestrator = OrchestratorAgent(gemini_api_key, self.catalog_manager)
        self.catalog_agents: Dict[str, CatalogAgent] = {}
    
    def add_catalog(self, filename: str, pdf_bytes: bytes) -> bool:
        """Add a new catalog to the system."""
        try:
            # Save PDF temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_bytes)
                tmp_path = tmp_file.name
            
            try:
                # Process PDF
                images = self.pdf_processor.pdf_to_images(tmp_path)
                content = self.pdf_processor.extract_full_content(images)
                summary = self.pdf_processor.generate_summary(images, filename)
                
                # Store in catalog manager
                self.catalog_manager.add_catalog(filename, content, summary, len(images))
                
                # Create catalog agent
                self.catalog_agents[filename] = CatalogAgent(
                    filename, content, self.gemini_api_key
                )
                
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
            selected_catalog = self.orchestrator.select_best_catalog(query)
            
            if not selected_catalog:
                return "No relevant catalogs found for your query.", "system"
            
            # Get detailed response from catalog agent
            if selected_catalog in self.catalog_agents:
                agent = self.catalog_agents[selected_catalog]
                detailed_response = agent.search_products(query)
                
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

# pdf_processor.py
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
import google.generativeai as genai
from typing import List

class PDFProcessor:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """Convert PDF to images."""
        try:
            pdf_document = fitz.open(pdf_path)
            images = []
            
            for page_num in range(min(pdf_document.page_count, 20)):  # Limit to 20 pages
                page = pdf_document[page_num]
                mat = fitz.Matrix(150/72, 150/72)  # Lower DPI for efficiency
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(BytesIO(img_data))
                images.append(img)
            
            pdf_document.close()
            return images
        except Exception as e:
            raise Exception(f"Error converting PDF: {str(e)}")
    
    def extract_full_content(self, images: List[Image.Image]) -> str:
        """Extract complete content from PDF images."""
        batch_size = 3
        all_content = []
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            
            prompt = f"""
            Extract ALL text and product information from these catalog pages.
            
            Include:
            - Product names and model numbers
            - Specifications and dimensions  
            - Prices and part numbers
            - Instructions and descriptions
            - Warranty information
            - Company details
            
            Format as clear, structured text with product sections.
            """
            
            try:
                response = self.model.generate_content([prompt] + batch)
                if hasattr(response, 'text') and response.text:
                    all_content.append(f"=== Pages {i+1}-{min(i+batch_size, len(images))} ===\n{response.text}")
            except Exception as e:
                all_content.append(f"Error extracting pages {i+1}-{min(i+batch_size, len(images))}: {str(e)}")
        
        return "\n\n".join(all_content)
    
    def generate_summary(self, images: List[Image.Image], filename: str) -> str:
        """Generate catalog summary for selection."""
        sample_images = images[:min(5, len(images))]
        
        prompt = f"""
        Analyze this catalog and create a brief summary.
        
        Include:
        - Main product categories
        - Types of products offered
        - Target market/industry
        - Key brands if visible
        - Specializations
        
        Keep it concise (2-3 sentences) but specific enough to distinguish from other catalogs.
        """
        
        try:
            response = self.model.generate_content([prompt] + sample_images)
            if hasattr(response, 'text') and response.text:
                return response.text
            return f"Product catalog: {filename}"
        except Exception as e:
            return f"Product catalog: {filename} - Summary generation failed"

# catalog_manager.py
from typing import Dict
from dataclasses import dataclass

@dataclass
class CatalogInfo:
    filename: str
    content: str
    summary: str
    page_count: int

class CatalogManager:
    def __init__(self):
        self.catalogs: Dict[str, CatalogInfo] = {}
    
    def add_catalog(self, filename: str, content: str, summary: str, page_count: int):
        """Add catalog to the manager."""
        self.catalogs[filename] = CatalogInfo(filename, content, summary, page_count)
    
    def get_catalog_content(self, filename: str) -> str:
        """Get full catalog content."""
        if filename in self.catalogs:
            return self.catalogs[filename].content
        return ""
    
    def get_catalog_summary(self, filename: str) -> str:
        """Get catalog summary."""
        if filename in self.catalogs:
            return self.catalogs[filename].summary
        return ""
    
    def get_all_summaries(self) -> str:
        """Get formatted summaries of all catalogs."""
        if not self.catalogs:
            return "No catalogs available."
        
        result = f"**📚 Available Catalogs ({len(self.catalogs)}):**\n\n"
        
        for i, (filename, info) in enumerate(self.catalogs.items(), 1):
            result += f"**{i}. {filename}**\n"
            result += f"   📄 Pages: {info.page_count}\n"
            result += f"   📋 Summary: {info.summary}\n\n"
        
        return result

# orchestrator_agent.py
import google.generativeai as genai
from catalog_manager import CatalogManager

class OrchestratorAgent:
    def __init__(self, gemini_api_key: str, catalog_manager: CatalogManager):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.catalog_manager = catalog_manager
    
    def select_best_catalog(self, query: str) -> str:
        """Select the most relevant catalog for the query."""
        if not self.catalog_manager.catalogs:
            return None
        
        if len(self.catalog_manager.catalogs) == 1:
            return list(self.catalog_manager.catalogs.keys())[0]
        
        # Create catalog options text
        catalog_options = ""
        for i, (filename, info) in enumerate(self.catalog_manager.catalogs.items(), 1):
            catalog_options += f"{i}. **{filename}**: {info.summary}\n"
        
        prompt = f"""
        Select the most relevant catalog for this query: "{query}"
        
        Available catalogs:
        {catalog_options}
        
        Respond with ONLY the catalog filename (including .pdf extension) that best matches the query.
        Consider product types, categories, and specializations mentioned in the summaries.
        """
        
        try:
            response = self.model.generate_content(prompt)
            if hasattr(response, 'text') and response.text:
                selected = response.text.strip()
                
                # Find matching catalog name
                for catalog_name in self.catalog_manager.catalogs.keys():
                    if catalog_name.lower() in selected.lower() or selected.lower() in catalog_name.lower():
                        return catalog_name
                
                # Fallback: return first catalog
                return list(self.catalog_manager.catalogs.keys())[0]
            
        except Exception as e:
            print(f"Error in catalog selection: {e}")
        
        # Fallback: return first available catalog
        return list(self.catalog_manager.catalogs.keys())[0]

# catalog_agent.py
import google.generativeai as genai

class CatalogAgent:
    def __init__(self, catalog_name: str, catalog_content: str, gemini_api_key: str):
        self.catalog_name = catalog_name
        self.catalog_content = catalog_content
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def search_products(self, query: str) -> str:
        """Search for products in the catalog content."""
        # Limit content size to prevent API issues
        content_preview = self.catalog_content[:20000]  # First 20k characters
        
        prompt = f"""
        Search this catalog for information about: "{query}"
        
        Catalog content:
        {content_preview}
        
        Provide detailed information including:
        - Exact product names and model numbers
        - Complete specifications and dimensions
        - Pricing information if available
        - Usage instructions if mentioned
        - Warranty details if provided
        - Part numbers or SKUs
        - Any safety information
        
        Be specific and include all relevant details found in the catalog.
        If multiple related products are found, list them all.
        """
        
        try:
            response = self.model.generate_content(prompt)
            if hasattr(response, 'text') and response.text:
                return response.text
            else:
                return self._fallback_text_search(query)
        except Exception as e:
            print(f"API search failed: {e}")
            return self._fallback_text_search(query)
    
    def _fallback_text_search(self, query: str) -> str:
        """Simple text-based search as fallback."""
        query_words = query.lower().split()
        content_lower = self.catalog_content.lower()
        
        # Find relevant sections
        lines = self.catalog_content.split('\n')
        relevant_lines = []
        
        for line in lines:
            if any(word in line.lower() for word in query_words):
                relevant_lines.append(line.strip())
        
        if relevant_lines:
            # Get surrounding context for better results
            result = f"**Found information about '{query}':**\n\n"
            
            # Group related lines together
            current_section = []
            for line in relevant_lines[:20]:  # Limit results
                if line:
                    current_section.append(line)
            
            result += '\n'.join(current_section)
            result += f"\n\n*Found in catalog: {self.catalog_name}*"
            return result
        else:
            return f"No specific information found for '{query}' in {self.catalog_name}. Try different keywords or browse the catalog overview."

