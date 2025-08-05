"""Configuration module for the Multi-Catalog System."""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(verbose=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model Configuration
AGENT_LLM_NAME = "gemini-2.5-flash"
GEMINI_MODEL_NAME = "gemini-2.5-flash"

# Processing Configuration
PDF_DPI = 200
BATCH_SIZE = 10
MAX_ANALYSIS_LENGTH = 20000
MAX_CONSOLIDATION_LENGTH = 12000

# Storage Configuration
DEFAULT_STORAGE_DIR = "catalog_storage"
METADATA_FILENAME = "catalog_metadata.pkl"

# Search Configuration
DEFAULT_TOP_K = 3
MAX_CATALOGS = 300

# Streamlit Configuration
STREAMLIT_CONFIG = {
    "page_title": "Multi-PDF Catalog System with Orchestrator Agent",
    "page_icon": "🤖",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}