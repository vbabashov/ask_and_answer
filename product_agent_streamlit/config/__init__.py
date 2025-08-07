# # File: config/__init__.py
# from .settings import Config

# __all__ = ['Config']


"""
Configuration package for the Multi-Catalog System
"""

from .settings import AGENT_LLM_NAME, setup_logging, disable_agents_tracing, setup_environment

__all__ = [
    'AGENT_LLM_NAME',
    'setup_logging', 
    'disable_agents_tracing',
    'setup_environment'
]