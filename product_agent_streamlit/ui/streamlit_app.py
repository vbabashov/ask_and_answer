"""Streamlit UI for the Multi-Catalog System."""

import asyncio
import os
import time
import streamlit as st
import nest_asyncio

from system.multi_catalog_system import MultiCatalogSystem
from config import STREAMLIT_CONFIG

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()


class StreamlitApp:
    """Streamlit application wrapper for the Multi-Catalog System."""
    
    def __init__(self):
        self.setup_page_config()
        
    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(**STREAMLIT_CONFIG)
    
    def render_sidebar(self):
        """Render the sidebar with configuration and controls."""
        with st.sidebar:
            st.header("⚙️ Configuration")
            
            # API Keys section
            gemini_api_key, openai_api_key = self._render_api_keys_section()
            
            if not gemini_api_key or not openai_api_key:
                st.warning("⚠️ Please provide both API keys to continue.")
                st.stop()
            
            st.divider()
            
            # File upload section
            uploaded_files = self._render_file_upload_section()
            
            st.divider()
            
            # System status section
            self._render_system_status_section()
            
            st.divider()
            
            # Quick actions section
            self._render_quick_actions_section()
            
            return gemini_api_key, openai_api_key, uploaded_files
    
    def _render_api_keys_section(self):
        """Render API keys input section."""
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
        
        return gemini_api_key, openai_api_key
    
    def _render_file_upload_section(self):
        """Render file upload section."""
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
        
        return uploaded_files
    
    def _render_system_status_section(self):
        """Render system status section."""
        if 'multi_system' in st.session_state and st.session_state.multi_system:
            st.subheader("📊 System Status")
            stats = st.session_state.multi_system.get_system_stats()
            st.metric("Catalogs Loaded", stats["total_catalogs"])
            st.metric("Active Agents", stats["active_agents"])
            
            if stats["total_catalogs"] > 0:
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
    
    def _render_quick_actions_section(self):
        """Render quick actions section."""
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
    
    def initialize_session_state(self):
        """Initialize Streamlit session state."""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'multi_system' not in st.session_state:
            st.session_state.multi_system = None
        
        if 'processed_files' not in st.session_state:
            st.session_state.processed_files = set()
    
    def initialize_system(self, gemini_api_key: str, openai_api_key: str):
        """Initialize the multi-catalog system."""
        if st.session_state.multi_system is None:
            try:
                st.session_state.multi_system = MultiCatalogSystem(gemini_api_key, openai_api_key)
                if not st.session_state.messages:
                    welcome_msg = self._get_welcome_message()
                    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
            except Exception as e:
                st.error(f"❌ Error initializing system: {str(e)}")
                st.stop()
    
    def _get_welcome_message(self) -> str:
        """Get welcome message for new users."""
        return """Hello! I'm your Multi-Catalog Orchestrator Agent. I can help you navigate through multiple product catalogs.

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
    
    def handle_file_uploads(self, uploaded_files):
        """Handle file uploads and processing."""
        if uploaded_files:
            new_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files]
            
            if new_files:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, file in enumerate(new_files):
                    status_text.text(f"Processing {file.name}... ({i+1}/{len(new_files)})")
                    progress_bar.progress((i) / len(new_files))
                    
                    try:
                        result = asyncio.run(
                            st.session_state.multi_system.add_catalog(file)
                        )
                        st.session_state.processed_files.add(file.name)
                        
                    except Exception as e:
                        st.error(f"❌ Error processing {file.name}: {str(e)}")
                        continue
                
                progress_bar.progress(1.0)
                status_text.text("✅ All files processed!")
                
                # Update messages
                catalog_count = st.session_state.multi_system.catalog_library.get_catalog_count()
                success_msg = f"✅ Successfully processed {len(new_files)} new catalog(s)! Total catalogs: {catalog_count}"
                st.session_state.messages.append({"role": "assistant", "content": success_msg})
                
                # Clear progress indicators after a moment
                time.sleep(2)
                progress_bar.empty()
                status_text.empty()
                
                st.rerun()
    
    def handle_quick_actions(self):
        """Handle quick action buttons."""
        if 'quick_action' in st.session_state and st.session_state.multi_system:
            quick_questions = {
                "library_overview": "Give me an overview of all available catalogs in the library",
                "search_all": "What types of products are available across all catalogs?",
                "recommendations": "What are some popular or featured products across the catalogs?"
            }
            
            question = quick_questions.get(st.session_state.quick_action)
            if question:
                st.session_state.messages.append({"role": "user", "content": question})
                
                with st.spinner("🤔 Processing quick action..."):
                    try:
                        response = asyncio.run(
                            st.session_state.multi_system.process_query(question)
                        )
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})
            
            # Clear quick action
            del st.session_state.quick_action
            st.rerun()
    
    def render_main_content(self):
        """Render the main content area."""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self._render_chat_interface()
        
        with col2:
            self._render_catalog_library()
    
    def _render_chat_interface(self):
        """Render the chat interface."""
        st.subheader("💬 Chat with Your Catalog Library")
        
        # Chat history container
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Chat input
        if st.session_state.multi_system:
            if prompt := st.chat_input("Ask about products across any catalog, or request specific comparisons..."):
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Get and display assistant response
                with st.chat_message("assistant"):
                    with st.spinner("🤔 Analyzing query, selecting best catalog, and generating response..."):
                        try:
                            response = asyncio.run(
                                st.session_state.multi_system.process_query(prompt)
                            )
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        except Exception as e:
                            error_msg = f"Sorry, I encountered an error: {str(e)}"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            st.info("👆 System initializing... Please wait.")
    
    def _render_catalog_library(self):
        """Render the catalog library sidebar."""
        st.subheader("📚 Catalog Library")
        
        if st.session_state.multi_system and st.session_state.multi_system.catalog_library.catalogs:
            for filename, metadata in st.session_state.multi_system.catalog_library.catalogs.items():
                with st.expander(f"📄 {filename}", expanded=False):
                    st.write(f"**Summary:** {metadata.summary}")
                    st.write(f"**Categories:** {', '.join(metadata.categories)}")
                    st.write(f"**Product Types:** {', '.join(metadata.product_types)}")
                    st.write(f"**Keywords:** {', '.join(metadata.keywords)}")
                    st.write(f"**Pages:** {metadata.page_count}")
                    
                    if st.button(f"Ask about {filename}", key=f"ask_{filename}"):
                        question = f"What products are available in {filename}?"
                        st.session_state.messages.append({"role": "user", "content": question})
                        st.rerun()
        else:
            st.info("No catalogs loaded yet. Upload PDF files to see them here.")
        
        st.divider()
        
        # System statistics
        if st.session_state.multi_system:
            st.subheader("📊 Statistics")
            stats = st.session_state.multi_system.get_system_stats()
            
            col_a, col_b = st.columns(2)
            col_a.metric("Catalogs", stats["total_catalogs"])
            col_b.metric("Agents", stats["active_agents"])
            st.metric("Messages", len(st.session_state.messages))
    
    def render_clear_chat_button(self):
        """Render clear chat button."""
        if st.session_state.messages:
            if st.button("🗑️ Clear Chat History"):
                st.session_state.messages = []
                st.rerun()
    
    def render_example_questions(self):
        """Render example questions section."""
        if st.session_state.multi_system and st.session_state.multi_system.catalog_library.catalogs:
            with st.expander("💡 Example Questions", expanded=False):
                examples = [
                    "What information do you have on Temperature Glass Kettle?",
                    "Show me all kettles available",
                    "What coffee makers do you have?",
                    "Find me wireless headphones under $100",
                    "What kitchen appliances are available?",
                    "Compare different espresso machines",
                    "Show me products on sale or discounted",
                    "What's the most expensive item across all catalogs?",
                    "Find eco-friendly products",
                    "What electronics are available?"
                ]
                
                cols = st.columns(2)
                for i, example in enumerate(examples):
                    col = cols[i % 2]
                    if col.button(example, key=f"example_{i}"):
                        st.session_state.messages.append({"role": "user", "content": example})
                        with st.spinner("Processing..."):
                            try:
                                response = asyncio.run(
                                    st.session_state.multi_system.process_query(example)
                                )
                                st.session_state.messages.append({"role": "assistant", "content": response})
                                st.rerun()
                            except Exception as e:
                                st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})
                                st.rerun()
    
    def render_features_showcase(self):
        """Render features showcase when no catalogs are loaded."""
        if not st.session_state.multi_system or not st.session_state.multi_system.catalog_library.catalogs:
            st.markdown("---")
            st.subheader("🚀 System Features")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                ### 🧠 Smart Orchestrator
                - Automatically selects best catalog
                - Understands query context
                - Routes to specialized agents
                - Provides comprehensive answers
                """)
            
            with col2:
                st.markdown("""
                ### 📚 Multi-Catalog Management
                - Support for up to 300 PDFs
                - Automatic metadata generation
                - Smart catalog categorization
                - Persistent storage system
                """)
            
            with col3:
                st.markdown("""
                ### 🔍 Advanced Search
                - Cross-catalog product search
                - Semantic understanding
                - Product comparisons
                - Contextual recommendations
                """)
            
            st.markdown("---")
            st.subheader("📋 How It Works")
            st.markdown("""
            1. **Upload Catalogs**: Add multiple PDF catalogs to your library
            2. **Automatic Processing**: Each catalog is analyzed and categorized
            3. **Smart Query Processing**: Ask any question and the system automatically:
               - Selects the most relevant catalog
               - Uses specialized agent to analyze that catalog
               - Provides detailed, accurate answers
            4. **Seamless Experience**: Get comprehensive responses without manual catalog selection
            """)
    
    def run(self):
        """Run the Streamlit application."""
        # Title and description
        st.title("🤖 Multi-PDF Catalog System with Orchestrator Agent")
        st.markdown("Upload multiple product catalog PDFs and chat with an AI orchestrator that selects the most appropriate catalog for your queries!")
        
        # Initialize session state
        self.initialize_session_state()
        
        # Render sidebar and get configuration
        gemini_api_key, openai_api_key, uploaded_files = self.render_sidebar()
        
        # Initialize system
        self.initialize_system(gemini_api_key, openai_api_key)
        
        # Handle file uploads
        self.handle_file_uploads(uploaded_files)
        
        # Handle quick actions
        self.handle_quick_actions()
        
        # Render main content
        self.render_main_content()
        
        # Clear chat button
        self.render_clear_chat_button()
        
        # Example questions
        self.render_example_questions()
        
        # Features showcase
        self.render_features_showcase()


def create_streamlit_app():
    """Create and run the Streamlit app."""
    app = StreamlitApp()
    app.run()