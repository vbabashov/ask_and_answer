import streamlit as st
import os
from pathlib import Path

from core.multi_catalog_system import MultiCatalogSystem
from dotenv import load_dotenv

load_dotenv()


def main():
    st.set_page_config(page_title="Multi-Catalog Search", layout="wide")
    
    st.title("🔍 Multi-Catalog Product Search")
    st.markdown("Upload product catalogs and search across them for detailed product information.")
    
    # Check for required API keys
    if not os.getenv('GEMINI_API_KEY'):
        st.error("Please set GEMINI_API_KEY environment variable")
        return
    
    if not os.getenv('OPENAI_API_KEY'):
        st.warning("OPENAI_API_KEY not found. Agent functionality will be limited.")
    
    # Initialize session state
    if 'system' not in st.session_state:
        st.session_state.system = MultiCatalogSystem(
            os.getenv('GEMINI_API_KEY'),
            os.getenv('OPENAI_API_KEY')
        )
    
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
            
            # Directly assign response to final_output
            final_output = response if response else "No detailed information found."
            
            # Display results
            if selected_catalog and selected_catalog != "system":
                st.success(f"🎯 Found information in: **{selected_catalog}**")
            
            st.markdown("### Search Results:")
            st.markdown(final_output)
    
    # Show catalog summaries
    if st.button("Show All Catalog Summaries"):
        summaries = system.get_all_catalog_summaries()
        st.markdown("### Catalog Library Overview:")
        st.markdown(summaries)

if __name__ == "__main__":
    main()