"""
Orchestrator agent that selects appropriate catalogs and answers queries
"""

from typing import Tuple, Optional
import agents
from openai import AsyncOpenAI

from config.settings import AGENT_LLM_NAME
from processors.pdf_processor import PDFCatalogProcessor
from storage.catalog_library import CatalogLibrary
from tools.orchestrator_tools import OrchestratorTools

class OrchestratorAgent:
    """Orchestrator agent that selects appropriate catalogs and answers queries."""
    
    def __init__(self, gemini_api_key: str, openai_client: AsyncOpenAI, catalog_library: CatalogLibrary, multi_system):
        self.processor = PDFCatalogProcessor(gemini_api_key)
        self.openai_client = openai_client
        self.catalog_library = catalog_library
        self.multi_system = multi_system  # Reference to MultiCatalogSystem
        self.tools = OrchestratorTools(catalog_library, self.processor, multi_system)
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the orchestrator agent."""
        catalog_summary = self.catalog_library.get_catalog_summaries()
        print(f"\n=== ORCHESTRATOR INITIALIZATION ===")
        print(f"Available catalogs summary:\n{catalog_summary}")
        
        self.agent = agents.Agent(
            name="Catalog Orchestrator",
            instructions=f"""
            You are the Catalog Orchestrator Agent. Your primary job is to answer user questions by:
            1. Selecting the most relevant catalog for the user's query
            2. Using that catalog to provide detailed answers

            For ANY product-related question, use the "answer_query_with_best_catalog" tool which will:
            - Find the most relevant catalog based on product types, categories, and keywords
            - Get detailed information from that catalog
            - Return a comprehensive answer

            Available Catalogs:
            {catalog_summary}

            When a user asks about products, features, specifications, prices, or any catalog-related information:
            - ALWAYS use the answer_query_with_best_catalog tool first
            - This tool will automatically select the best catalog and provide the detailed answer
            - The tool includes fallback logic to try multiple catalogs if needed
            - Do not use other tools unless specifically asked for catalog overviews or searches

            Be helpful and conversational, but always rely on the tools to provide accurate information.
            Focus on getting the best possible answer from the most relevant catalog.
            """,
            tools=[
                agents.function_tool(self.tools.answer_query_with_best_catalog),
                agents.function_tool(self.tools.search_catalogs),
                agents.function_tool(self.tools.get_catalog_overview),
            ],
            model=agents.OpenAIChatCompletionsModel(
                model=AGENT_LLM_NAME,
                openai_client=self.openai_client
            ),
        )
    
    async def chat_response(self, question: str) -> Tuple[str, Optional[str]]:
        if not self.agent:
            return "❌ Orchestrator not initialized.", None

        try:
            print(f"\n=== ORCHESTRATOR CHAT ===")
            print(f"Question: {question}")
            
            result = await agents.Runner.run(self.agent, input=question)
            print("DEBUG: Agent result:", result)

            # Extract the response text
            response_text = ""
            if hasattr(result, 'messages') and result.messages:
                for message in reversed(result.messages):
                    if hasattr(message, 'role') and message.role == 'assistant':
                        if hasattr(message, 'content'):
                            if isinstance(message.content, str) and message.content.strip():
                                response_text = message.content
                                break
                            elif isinstance(message.content, list):
                                text_parts = []
                                for content_block in message.content:
                                    if hasattr(content_block, 'text') and content_block.text.strip():
                                        text_parts.append(content_block.text)
                                if text_parts:
                                    response_text = ' '.join(text_parts)
                                    break

            # Fallback handling
            if not response_text and hasattr(result, 'output') and result.output:
                response_text = str(result.output)
            if not response_text and hasattr(result, 'final_output') and result.final_output:
                response_text = str(result.final_output)

            # Try to identify which catalog was selected
            selected_catalog = None
            if "Selected Catalog:" in response_text:
                for catalog_name in self.catalog_library.catalogs.keys():
                    if catalog_name in response_text:
                        selected_catalog = catalog_name
                        break

            return response_text or "No response from agent.", selected_catalog

        except Exception as e:
            print(f"Error in orchestrator chat: {str(e)}")
            return f"Error from orchestrator: {str(e)}", None