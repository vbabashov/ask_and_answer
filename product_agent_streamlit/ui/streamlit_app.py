# File: ui/streamlit_app.py
import asyncio
from datetime import datetime

def create_streamlit_app():
    """Create Streamlit interface"""
    # Import streamlit inside the function
    import streamlit as st
    
    st.set_page_config(
        page_title="Multi-PDF Catalog System",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🤖 Multi-PDF Catalog System with Orchestrator Agent")
    st.markdown("Upload multiple product catalog PDFs and chat with an AI orchestrator!")
    
    # Import here to avoid circular imports and context issues
    try:
        from config import Config
        from main import CatalogSystemFacade
    except ImportError as e:
        st.error(f"Import error: {e}")
        st.stop()
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'system' not in st.session_state:
        st.session_state.system = None
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Load configuration
        config = Config()
        
        # API Keys section
        st.subheader("API Keys")
        if config.gemini_api_key:
            st.success("✅ Gemini API key loaded")
        else:
            config.gemini_api_key = st.text_input(
                "Gemini API Key", type="password",
                help="Get your API key from https://makersuite.google.com/app/apikey"
            )
        
        if config.openai_api_key:
            st.success("✅ OpenAI API key loaded")
        else:
            config.openai_api_key = st.text_input(
                "OpenAI API Key", type="password",
                help="Get your API key from https://platform.openai.com/api-keys"
            )
        
        if not config.validate():
            st.warning("⚠️ Please provide both API keys to continue.")
            st.stop()
        
        st.divider()
        
        # File upload
        st.subheader("📄 PDF Upload")
        uploaded_files = st.file_uploader(
            "Upload PDF Catalogs",
            type=['pdf'],
            accept_multiple_files=True,
            help=f"Upload up to {config.max_catalogs} catalog PDFs"
        )
        
        if uploaded_files:
            st.success(f"📄 {len(uploaded_files)} PDF(s) selected")
            total_size = sum(file.size for file in uploaded_files) / 1024 / 1024
            st.info(f"Total size: {total_size:.1f} MB")
        
        st.divider()
        
        # System status
        if st.session_state.system:
            st.subheader("📊 System Status")
            try:
                catalog_count = st.session_state.system.get_catalog_count()
                agent_count = st.session_state.system.get_agent_count()
                
                st.metric("Catalogs Loaded", catalog_count)
                st.metric("Active Agents", agent_count)
                
                if catalog_count > 0:
                    if st.button("🔄 Refresh System", use_container_width=True):
                        st.session_state.system.agent_service.refresh_orchestrator()
                        st.success("System refreshed!")
                        st.rerun()
            except Exception as e:
                st.error(f"Error getting system status: {e}")
    
    # Initialize system with proper error handling
    if st.session_state.system is None:
        try:
            with st.spinner("Initializing system..."):
                st.session_state.system = CatalogSystemFacade(config)
            
            # Welcome message
            if not st.session_state.messages:
                welcome_msg = """Hello! I'm your Multi-Catalog Orchestrator Agent. 

**How it works:**
1. Upload your PDF catalogs using the sidebar
2. I'll analyze each catalog and understand what products they contain  
3. When you ask questions, I'll automatically select the most relevant catalog

**What you can ask:**
- "What coffee makers do you have?"
- "Show me kitchen appliances under $200"
- "Compare different laptop models"
- "Find wireless headphones"

Upload your catalogs to get started!"""
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": welcome_msg,
                    "timestamp": datetime.now()
                })
        except Exception as e:
            st.error(f"❌ Error initializing system: {str(e)}")
            st.stop()
    
    # Handle file uploads with better async handling
    if uploaded_files and st.session_state.system:
        new_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files]
        
        if new_files:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, file in enumerate(new_files):
                status_text.text(f"Processing {file.name}... ({i+1}/{len(new_files)})")
                progress_bar.progress(i / len(new_files))
                
                try:
                    # Use asyncio.run with proper context handling
                    result = asyncio.run(st.session_state.system.add_catalog(file))
                    st.session_state.processed_files.add(file.name)
                except Exception as e:
                    st.error(f"❌ Error processing {file.name}: {str(e)}")
                    continue
            
            progress_bar.progress(1.0)
            status_text.text("✅ All files processed!")
            
            # Success message
            success_msg = f"✅ Successfully processed {len(new_files)} new catalog(s)!"
            st.session_state.messages.append({
                "role": "assistant",
                "content": success_msg,
                "timestamp": datetime.now()
            })
            
            # Clear progress indicators after delay
            import time
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            st.rerun()
    
    # Main chat interface
    st.subheader("💬 Chat with Your Catalog Library")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if st.session_state.system and st.session_state.system.get_catalog_count() > 0:
        if prompt := st.chat_input("Ask about products across any catalog..."):
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now()
            })
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Processing your query..."):
                    try:
                        # Better async handling
                        response = asyncio.run(st.session_state.system.process_query(prompt))
                        st.markdown(response)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response,
                            "timestamp": datetime.now()
                        })
                    except Exception as e:
                        error_msg = f"Sorry, I encountered an error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg,
                            "timestamp": datetime.now()
                        })
    elif st.session_state.system:
        st.info("👆 Upload some PDF catalogs to start chatting!")
    else:
        st.info("👆 System initializing... Please wait.")
    
    # Sidebar catalog overview
    if st.session_state.system and st.session_state.system.get_catalog_count() > 0:
        with st.sidebar:
            st.divider()
            st.subheader("📚 Quick Actions")
            
            if st.button("📋 Library Overview", use_container_width=True):
                try:
                    overview = st.session_state.system.get_catalog_overview()
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": overview,
                        "timestamp": datetime.now()
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"Error getting overview: {e}")
            
            if st.button("💡 Example Questions", use_container_width=True):
                examples = """Here are some example questions you can ask:

• "What coffee makers do you have?"
• "Show me wireless headphones under $100"  
• "Find kitchen appliances on sale"
• "Compare different laptop models"
• "What electronics are available?"
• "Show me eco-friendly products"
• "Find the most expensive items"
• "What brands do you carry?"

Try asking about specific products or categories!"""
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": examples,
                    "timestamp": datetime.now()
                })
                st.rerun()
    
    # Clear chat button
    if st.session_state.messages and len(st.session_state.messages) > 1:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = st.session_state.messages[:1]  # Keep welcome message
            st.rerun()


# Alternative main execution approach
def main():
    """Main execution function"""
    create_streamlit_app()


if __name__ == "__main__":
    main()