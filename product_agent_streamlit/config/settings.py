"""
Configuration settings for the Multi-Catalog System
"""

import os
import logging
import nest_asyncio
from dotenv import load_dotenv

# Disable OpenAI Agents tracing via environment variable (before any imports)
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

# Agent configuration
AGENT_LLM_NAME = "gemini-2.5-flash"

def setup_environment():
    """Setup environment variables and configurations."""
    # Apply nest_asyncio to allow nested event loops
    nest_asyncio.apply()
    
    # Load environment variables
    load_dotenv(verbose=True)

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(level=logging.INFO)

def disable_agents_tracing():
    """Disable OpenAI agents tracing - already handled via environment variable."""
    print("OpenAI Agents tracing disabled via environment variable")
    pass

# Initialize environment on import
setup_environment()