"""
Multi-PDF Catalog System with Orchestrator Agent
Main entry point for the application
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import configuration
from config.settings import setup_logging, disable_agents_tracing
from ui.streamlit_app import create_streamlit_app

def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    
    # # Disable OpenAI agents tracing
    # disable_agents_tracing()
    
    # Create and run the Streamlit app
    create_streamlit_app()

if __name__ == "__main__":
    main()