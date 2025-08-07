# """
# Configuration settings for the Multi-Catalog System
# """

# import os
# import logging
# import nest_asyncio
# from dotenv import load_dotenv

# # Disable OpenAI Agents tracing via environment variable (before any imports)
# os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

# # Agent configuration
# AGENT_LLM_NAME = "gemini-2.5-flash"

# def setup_environment():
#     """Setup environment variables and configurations."""
#     # Apply nest_asyncio to allow nested event loops
#     nest_asyncio.apply()
    
#     # Load environment variables
#     load_dotenv(verbose=True)

# def setup_logging():
#     """Setup logging configuration."""
#     logging.basicConfig(level=logging.INFO)

# def disable_agents_tracing():
#     """Disable OpenAI agents tracing - already handled via environment variable."""
#     print("OpenAI Agents tracing disabled via environment variable")
#     pass

# # Initialize environment on import
# setup_environment()


"""
Configuration settings for the Multi-Catalog System with Gemini integration
"""

import os
import logging
import nest_asyncio
from dotenv import load_dotenv

# Disable OpenAI Agents tracing via environment variable (before any imports)
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

# Updated agent configuration - we'll use a placeholder since we're using Gemini
AGENT_LLM_NAME = "gemini-2.5-flash"  # This is for reference only
GEMINI_MODEL_NAME = "gemini-2.5-flash"  # Actual Gemini model

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

def create_gemini_client(gemini_api_key: str):
    """Create a Gemini client that works with OpenAI Agents SDK."""
    from adapters.gemini_model import GeminiChatModel
    return GeminiChatModel(model_name=GEMINI_MODEL_NAME, api_key=gemini_api_key)

# Initialize environment on import
setup_environment()