"""
Enhanced orchestrator agent with better catalog selection and fallback logic
Key improvements:
1. Try all catalogs until a good answer is found
2. Better response quality detection
3. Improved catalog ranking
4. Comprehensive fallback strategies
"""

import os
import agents
from openai import AsyncOpenAI
from typing import Tuple

from config.settings import AGENT_LLM_NAME
from storage.catalog_library import CatalogLibrary
from processors.pdf_processor import PDFCatalogProcessor


class OrchestratorTools:
    """Enhanced tools for the orchestrator agent."""
    
    def __init__(self, catalog_library: CatalogLibrary, processor: PDFCatalogProcessor, multi_system):
        self.catalog_library = catalog_library
        self.processor = processor
        self.multi_system = multi_system
    
    def _is_good_response(self, response: str, query: str) -> bool:
        """Determine if a response is useful/relevant."""
        response_lower = response.lower()
        query_lower = query.lower()
        
        # Negative indicators (bad response)
        negative_indicators = [
            "no information",
            "not found",
            "sorry",
            "cannot find",
            "unable to locate",
            "don't have information",
            "not available in this catalog",
            "no products matching",
            "error",
            "failed to"
        ]
        
        # Check if response contains negative indicators
        has_negative = any(indicator in response_lower for indicator in negative_indicators)
        
        # Positive indicators (good response)
        positive_indicators = [
            "$",  # Price information
            "specification",
            "feature",
            "model",
            "page",
            "product",
            "available",
            "includes",
            "warranty"
        ]
        
        has_positive = any(indicator in response_lower for indicator in positive_indicators)
        
        # Good response should have positive indicators and no/few negative ones
        # Also check response length (very short responses are usually not helpful)
        is_substantial = len(response.strip()) > 100
        
        # If query asks for specific product names, check if response mentions them
        query_words = query_lower.split()
        response_has_query_terms = any(word in response_lower for word in query_words if len(word) > 3)
        
        return (has_positive or response_has_query_terms) and not has_negative and is_substantial
    
    async def answer_query_with_best_catalog(self, query: str) -> str:
        """Enhanced query processing with comprehensive catalog testing."""
        try:
            print(f"\n=== ENHANCED ORCHESTRATOR PROCESSING ===")
            print(f"Query: {query}")
            print(f"Available catalogs: {list(self.catalog_library.catalogs.keys())}")
            
            # Get ranked catalogs
            relevant_catalogs = self.catalog_library.search_relevant_catalogs(query, self.processor, top_k=5)
            
            if not relevant_catalogs:
                return "❌ No catalogs available to search."
            
            print(f"Catalog rankings: {relevant_catalogs}")
            
            best_response = None
            best_catalog = None
            best_score = 0.0
            
            # Try catalogs in order of relevance
            for catalog_name, relevance_score in relevant_catalogs:
                print(f"\n--- Testing catalog: {catalog_name} (score: {relevance_score}) ---")
                
                try:
                    # Get the catalog agent
                    catalog_agent = await self.multi_system.get_catalog_agent(catalog_name)
                    
                    # Query the catalog
                    response = await catalog_agent.chat_response(query)
                    
                    print(f"Response preview: {response[:200]}...")
                    
                    # Check if this is a good response
                    is_good = self._is_good_response(response, query)
                    print(f"Response quality: {'GOOD' if is_good else 'POOR'}")
                    
                    if is_good:
                        print(f"✅ Found good response in catalog: {catalog_name}")
                        best_response = response
                        best_catalog = catalog_name
                        best_score = relevance_score
                        break  # Found a good answer, stop searching
                    else:
                        # Keep track of best response even if not ideal
                        if best_response is None:
                            best_response = response
                            best_catalog = catalog_name
                            best_score = relevance_score
                
                except Exception as e:
                    print(f"❌ Error querying catalog {catalog_name}: {str(e)}")
                    continue
            
            # If no good response found, try a different approach
            if best_response and not self._is_good_response(best_response, query):
                print(f"\n--- No good responses found, trying comprehensive search ---")
                
                # Try a more general search across all catalogs
                comprehensive_response = await self._comprehensive_search(query)
                if comprehensive_response:
                    return comprehensive_response
            
            # Format the final response
            if best_response and best_catalog:
                result = f"**Selected Catalog: {best_catalog}** (Relevance: {best_score:.1f}/10)\n\n"
                result += f"**Answer:**\n{best_response}"
                
                # Add disclaimer if response quality is poor
                if not self._is_good_response(best_response, query):
                    result += f"\n\n*Note: Limited information found. You may want to try a more specific query or check if the product is available in other catalogs.*"
                
                return result
            else:
                return "❌ Unable to find relevant information in any catalog. Please check your query or try uploading more specific catalogs."
                
        except Exception as e:
            print(f"Error in enhanced orchestrator: {str(e)}")
            return f"❌ Error processing query: {str(e)}"
    
    async def _comprehensive_search(self, query: str) -> str:
        """Perform comprehensive search across all catalogs with aggregated results."""
        try:
            print("Performing comprehensive search across all catalogs...")
            
            all_results = []
            
            for catalog_name in self.catalog_library.catalogs.keys():
                try:
                    catalog_agent = await self.multi_system.get_catalog_agent(catalog_name)
                    response = await catalog_agent.chat_response(query)
                    
                    # Only include responses that have some relevant content
                    if len(response.strip()) > 50 and not any(neg in response.lower() for neg in ["no information", "not found", "sorry"]):
                        all_results.append({
                            'catalog': catalog_name,
                            'response': response
                        })
                
                except Exception as e:
                    print(f"Error in comprehensive search for {catalog_name}: {e}")
                    continue
            
            if all_results:
                # Aggregate results
                result = f"**Comprehensive Search Results for: {query}**\n\n"
                result += f"Found relevant information in {len(all_results)} catalog(s):\n\n"
                
                for i, item in enumerate(all_results, 1):
                    result += f"**{i}. From Catalog: {item['catalog']}**\n"
                    result += f"{item['response']}\n"
                    result += "---\n\n"
                
                return result
            
            return None
                
        except Exception as e:
            print(f"Error in comprehensive search: {e}")
            return None
    
    async def search_catalogs(self, query: str) -> str:
        """Enhanced catalog search with detailed information."""
        try:
            relevant_catalogs = self.catalog_library.search_relevant_catalogs(query, self.processor, top_k=5)
            
            if not relevant_catalogs:
                return "No catalogs found matching your query."
            
            result = f"**Found {len(relevant_catalogs)} relevant catalogs for: '{query}'**\n\n"
            
            for i, (catalog_name, score) in enumerate(relevant_catalogs, 1):
                metadata = self.catalog_library.catalogs[catalog_name]
                result += f"**{i}. {catalog_name}** (Relevance: {score:.1f}/10)\n"
                result += f"   📋 **Summary:** {metadata.summary}\n"
                result += f"   🏷️ **Categories:** {', '.join(metadata.categories[:5])}\n"
                result += f"   📦 **Product Types:** {', '.join(metadata.product_types[:5])}\n"
                
                # Add product names if available
                if hasattr(metadata, 'product_names') and metadata.product_names:
                    result += f"   🔍 **Sample Products:** {', '.join(metadata.product_names[:3])}\n"
                
                # Add brand names if available  
                if hasattr(metadata, 'brand_names') and metadata.brand_names:
                    result += f"   🏢 **Brands:** {', '.join(metadata.brand_names[:3])}\n"
                
                result += f"   📄 **Pages:** {metadata.page_count}\n\n"
            
            result += "\n💡 **Tip:** Ask specific questions about products to get detailed information from the most relevant catalog."
            
            return result
            
        except Exception as e:
            return f"Error searching catalogs: {str(e)}"
    
    async def get_catalog_overview(self) -> str:
        """Enhanced catalog overview with better formatting."""
        try:
            if not self.catalog_library.catalogs:
                return "📚 **No catalogs available in the library.**\n\nPlease upload some PDF catalogs to get started!"
            
            overview = f"📚 **Catalog Library Overview**\n\n"
            overview += f"**Total Catalogs:** {len(self.catalog_library.catalogs)}\n"
            overview += f"**Total Pages:** {sum(metadata.page_count for metadata in self.catalog_library.catalogs.values())}\n\n"
            
            overview += "**Available Catalogs:**\n\n"
            
            for i, (filename, metadata) in enumerate(self.catalog_library.catalogs.items(), 1):
                overview += f"**{i}. {filename}**\n"
                overview += f"   📝 {metadata.summary}\n"
                overview += f"   🏷️ **Categories:** {', '.join(metadata.categories[:4])}\n"
                overview += f"   📦 **Product Types:** {', '.join(metadata.product_types[:4])}\n"
                
                # Show some keywords for searchability
                if metadata.keywords:
                    overview += f"   🔑 **Keywords:** {', '.join(metadata.keywords[:6])}\n"
                
                # Show product names if available
                if hasattr(metadata, 'product_names') and metadata.product_names:
                    overview += f"   🔍 **Sample Products:** {', '.join(metadata.product_names[:3])}\n"
                
                overview += f"   📄 **Pages:** {metadata.page_count}\n\n"
            
            overview += "\n**How to use:**\n"
            overview += "• Ask specific product questions (e.g., 'Show me coffee makers under $200')\n"
            overview += "• Request product comparisons (e.g., 'Compare laptop models')\n"
            overview += "• Search by category (e.g., 'What kitchen appliances do you have?')\n"
            overview += "• Ask for detailed specifications of specific products\n"
            
            return overview
            
        except Exception as e:
            return f"Error getting catalog overview: {str(e)}"


class OrchestratorAgent:
    """Enhanced orchestrator agent that manages multiple catalog agents."""
    
    def __init__(self, gemini_api_key: str, openai_client: AsyncOpenAI, catalog_library: CatalogLibrary, multi_system):
        self.processor = PDFCatalogProcessor(gemini_api_key)
        self.openai_client = openai_client
        self.catalog_library = catalog_library
        self.multi_system = multi_system
        self.tools = OrchestratorTools(catalog_library, self.processor, multi_system)
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the OpenAI orchestrator agent with Gemini model."""
        try:
            # Get current catalog information
            catalog_info = self._get_catalog_info()
            
            # Import the Gemini adapter
            from adapters.gemini_model import GeminiChatModel
            
            # Use the API key directly from the processor
            gemini_api_key = self.processor.gemini_api_key  # Ensure this is set during initialization
            
            # Create Gemini model instance
            gemini_model = GeminiChatModel(
                model_name="gemini-2.5-flash",  # Use the appropriate model name
                api_key=gemini_api_key,  # Pass the API key explicitly
                base_url=os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")  # Pass base URL
            )
            
            # Create a custom model wrapper for agents SDK
            class GeminiModelWrapper:
                def __init__(self, gemini_client):
                    self.gemini_client = gemini_client
                    self.base_url = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")  # Default base URL
                
                @property
                def chat(self):
                    return self
                
                @property
                def completions(self):
                    return self.gemini_client
            
            # Create the agent with Gemini model
            self.agent = agents.Agent(
                name="Multi-Catalog Orchestrator",
                instructions=f"""
                You are an expert Multi-Catalog Orchestrator Agent that helps users find products across multiple catalogs.
                
                **AVAILABLE CATALOGS:**
                {catalog_info}
                """,
                tools=[
                    agents.function_tool(self.tools.answer_query_with_best_catalog),
                    agents.function_tool(self.tools.search_catalogs),
                    agents.function_tool(self.tools.get_catalog_overview),
                ],
                model=agents.OpenAIChatCompletionsModel(
                    model="gemini",  # Placeholder name
                    openai_client=GeminiModelWrapper(gemini_model)
                ),
            )
            print("✅ Orchestrator agent initialized successfully with Gemini")
        except Exception as e:
            print(f"❌ Error initializing orchestrator agent: {e}")
            import traceback
            traceback.print_exc()
            self.agent = None
    
    def _get_catalog_info(self) -> str:
        """Get formatted information about available catalogs."""
        if not self.catalog_library.catalogs:
            return "No catalogs currently available."
        
        info = f"Currently managing {len(self.catalog_library.catalogs)} catalogs:\n"
        for filename, metadata in self.catalog_library.catalogs.items():
            info += f"- {filename}: {metadata.summary[:100]}...\n"
            info += f"  Categories: {', '.join(metadata.categories[:3])}\n"
            info += f"  Products: {', '.join(getattr(metadata, 'product_types', [])[:3])}\n"
        
        return info
    
    async def chat_response(self, question: str) -> Tuple[str, str]:
        """Get response from orchestrator agent."""
        try:
            print(f"\n=== ORCHESTRATOR CHAT RESPONSE ===")
            print(f"Question: {question}")
            print(f"Agent available: {self.agent is not None}")
            
            if not self.agent:
                print("No agent available, reinitializing...")
                self._initialize_agent()
                if not self.agent:
                    return "❌ Orchestrator agent is not available. Please check your configuration.", "system"
            
            # Use the agent to process the query
            result = await agents.Runner.run(self.agent, input=question)
            
            # Extract response text
            response_text = ""
            selected_catalog = "orchestrator"
            
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
            
            # Try final_output if available
            if not response_text and hasattr(result, 'final_output'):
                response_text = str(result.final_output)
            
            # Extract catalog name from response if present
            if "Selected Catalog:" in response_text:
                try:
                    selected_catalog = response_text.split("Selected Catalog:")[1].split("**")[0].strip()
                except:
                    selected_catalog = "orchestrator"
            
            return response_text or "I'm having trouble processing that request. Please try rephrasing your question.", selected_catalog
            
        except Exception as e:
            error_msg = f"❌ Error in orchestrator response: {str(e)}"
            print(error_msg)
            return error_msg, "system"