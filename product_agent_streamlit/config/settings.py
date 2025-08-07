"""
Configuration settings for the Multi-Catalog System
"""

import logging
import nest_asyncio
import agents
from dotenv import load_dotenv

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
    """Disable OpenAI agents tracing."""
    agents.set_tracing_disabled(disabled=True)

# Initialize environment on import
setup_environment()