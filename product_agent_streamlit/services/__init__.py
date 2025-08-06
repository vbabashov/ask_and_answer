# # File: services/__init__.py
# from .gemini_service import GeminiService
# from .catalog_service import CatalogService
# from .agent_service import AgentService, CatalogAgent, OrchestratorAgent

# __all__ = ['GeminiService', 'CatalogService', 'AgentService', 'CatalogAgent', 'OrchestratorAgent']

# File: services/__init__.py
from .gemini_service import GeminiService
from .catalog_service import CatalogService
# from .agent_service import AgentService, CatalogAgent, OrchestratorAgent
from .improved_agent_service import OptimizedAgentService

__all__ = ['GeminiService', 'CatalogService', 'OptimizedAgentService']