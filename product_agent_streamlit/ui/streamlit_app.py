"""
Streamlit interface for the multi-PDF catalog system
"""

import asyncio
import os
import time
import streamlit as st

from core.multi_catalog_system import MultiCatalogSystem

# Streamlit App Configuration
st.set_page_config(
    page_title="Multi-PDF Catalog System with Orchestrator Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def create_streamlit_app():
    """Create Streamlit interface for the multi-PDF catalog system."""
    
    # Title and description
    st.title("🤖 Multi-PDF Catalog System with Orchestrator Agent")
    st.markdown("Upload multiple product catalog PDFs and chat with an AI orchestrator that selects the most appropriate catalog for your queries!")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Keys
        st.subheader("API Keys")
        
        # Check for environment variables first
        gemini_key_env = os.getenv("GEMINI_API_KEY")
        openai_key_env = os.getenv("OPENAI_API_KEY")
        
        if gemini_key_env:
            st.success("✅ Gemini API key loaded from environment")
            gemini_api_key = gemini_key_env
        else:
            gemini_api_key = st.text_input(
                "Gemini API Key",
                type="password",
                help="Get your API key from https://makersuite.google.com/app/apikey",
                placeholder="Enter your Gemini API key..."
            )
        
        if openai_key_env:
            st.success("✅ OpenAI API key loaded from environment")
            openai_api_key = openai_key_env
        else:
            openai_api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="Get your API key from https://platform.openai.com/api-keys",
                placeholder="Enter your OpenAI API key..."
            )
        
        if not gemini_api_key or not openai_api_key:
            st.warning("⚠️ Please provide both API keys to continue.")
            st.stop()
        
        st.divider()
        
        # File upload section
        st.subheader("📄 PDF Upload")
        uploaded_files = st.file_uploader(
            "Upload PDF Catalogs",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload multiple product catalog PDF files (max 300 PDFs)"
        )
        
        if uploaded_files:
            st.success(f"📄 {len(uploaded_files)} PDF(s) selected")
            total_size = sum(file.size for file in uploaded_files) / 1024 / 1024
            st.info(f"Total size: {total_size:.1f} MB")
            
            # Show list of uploaded files
            with st.expander("📋 Uploaded Files", expanded=False):
                for i, file in enumerate(uploaded_files, 1):
                    st.write(f"{i}. {file.name} ({file.size / 1024 / 1024:.1f} MB)")
        
        st.divider()
        
        # System status
        if 'multi_system' in st.session_state and st.session_state.multi_system:
            st.subheader("📊 System Status")
            catalog_count = len(st.session_state.multi_system.catalog_library.catalogs)
            st.metric("Catalogs Loaded", catalog_count)
            st.metric("Active Agents", len(st.session_state.multi_system.catalog_agents))
            
            if catalog_count > 0:
                if st.button("🔄 Refresh Orchestrator", use_container_width=True):
                    st.session_state.multi_system.orchestrator._initialize_agent()
                    st.success("Orchestrator refreshed!")
                    st.rerun()
                
                # Show catalog summaries for debugging
                with st.expander("🔍 Debug: Catalog Details", expanded=False):
                    for name, metadata in st.session_state.multi_system.catalog_library.catalogs.items():
                        st.write(f"**{name}**")
                        st.write(f"Summary: {metadata.summary}")
                        st.write(f"Categories: {metadata.categories}")
                        st.write(f"Product Types: {metadata.product_types}")
                        st.write(f"Keywords: {metadata.keywords}")
                        st.write("---")
        
        st.divider()
        
        # Quick actions
        if 'multi_system' in st.session_state and st.session_state.multi_system:
            st.subheader("🚀 Quick Actions")
            
            if st.button("📋 Library Overview", use_container_width=True):
                st.session_state.quick_action = "library_overview"
                st.rerun()
            
            if st.button("🔍 Search All Catalogs", use_container_width=True):
                st.session_state.quick_action = "search_all"
                st.rerun()
            
            if st.button("💡 Get Recommendations", use_container_width=True):
                st.session_state.quick_action = "recommendations"
                st.rerun()
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'multi_system' not in st.session_state:
        st.session_state.multi_system = None
    
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()
    
    # Initialize system if not already done
    if st.session_state.multi_system is None:
        try:
            st.session_state.multi_system = MultiCatalogSystem(gemini_api_key, openai_api_key)
            if not st.session_state.messages:
                welcome_msg = """Hello! I'm your Multi-Catalog Orchestrator Agent. I can help you navigate through multiple product catalogs.

**How it works:**
1. Upload your PDF catalogs (up to 300 PDFs)
2. I'll analyze each catalog and understand what products they contain
3. When you ask questions, I'll automatically select the most relevant catalog and provide detailed answers

**What you can ask:**
- "What information do you have on programmable coffee makers?"
- "Show me kitchen appliances under $200"
- "What's the name of the coffee machine in the manual?"
- "Compare different laptop models"

Upload your catalogs to get started!"""
                st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
        except Exception as e:
            st.error(f"❌ Error initializing system: {str(e)}")
            st.stop()
    
    # Handle file uploads
    if uploaded_files:
        new_files = [f for f in uploaded_files if f.name not in