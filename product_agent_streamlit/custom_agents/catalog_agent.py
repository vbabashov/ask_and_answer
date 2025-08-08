# catalog_agent.py
import asyncio
from agents import Agent, function_tool,OpenAIChatCompletionsModel, Runner

class CatalogAgent:
    def __init__(self, catalog_name: str, catalog_content: str, gemini_api_key: str, async_openai_client):
        self.catalog_name = catalog_name
        self.catalog_content = catalog_content
        self.async_openai_client = async_openai_client
        
        # Define tools for the agent
        self.tools = [
            function_tool(self._search_products_tool),
            function_tool(self._get_catalog_overview_tool),
        ]
        
        # Initialize the agent
        self.agent = Agent(
            name=f"Catalog Agent - {self.catalog_name}",
            instructions=f"""
            You are an expert catalog agent for the catalog: {self.catalog_name}.
            Use the tools provided to search for products and provide detailed information.
            Always base your responses on the actual catalog content.
            Provide comprehensive and accurate product information including specifications, prices, and part numbers when available.
            """,
            tools=self.tools,
            model=OpenAIChatCompletionsModel(
                model="gemini-2.5-flash",
                openai_client=self.async_openai_client,
            ),
        )
    
    async def _search_products_tool(self, query: str) -> str:
        """Tool function to search for products in the catalog content."""
        content_preview = self.catalog_content[:15000]  # Limit content size
        
        # Perform actual search logic
        query_words = query.lower().split()
        content_lower = self.catalog_content.lower()
        
        # Find relevant sections
        lines = self.catalog_content.split('\n')
        relevant_lines = []
        
        for line in lines:
            if any(word in line.lower() for word in query_words):
                relevant_lines.append(line.strip())
        
        if relevant_lines:
            result = f"Found information about '{query}':\n\n"
            result += '\n'.join(relevant_lines[:20])  # Limit results
            return result
        else:
            return f"No specific information found for '{query}' in the catalog content."
    
    async def _get_catalog_overview_tool(self) -> str:
        """Tool function to provide an overview of the catalog."""
        content_preview = self.catalog_content[:10000]  # First 10k characters
        
        # Extract key information
        lines = content_preview.split('\n')
        products_mentioned = []
        
        for line in lines[:100]:  # Check first 100 lines
            if any(keyword in line.lower() for keyword in ['model', 'part', 'item', 'product']):
                if line.strip() and len(line.strip()) > 5:
                    products_mentioned.append(line.strip())
        
        overview = f"Catalog Overview for {self.catalog_name}:\n"
        overview += f"Contains approximately {len(products_mentioned)} product entries.\n"
        
        if products_mentioned:
            overview += f"Sample products: {products_mentioned[:3]}"
        
        return overview
    
    async def search_products_sync(self, query: str) -> str:
        """Synchronous wrapper for searching products using the agent."""
        try:
            # Use the agent to process the query
            run_result = await Runner.run(self.agent, input=query)
            
            # Extract the final output from RunResult
            if hasattr(run_result, 'final_output') and run_result.final_output:
                return run_result.final_output
            elif hasattr(run_result, 'content') and run_result.content:
                return run_result.content
            else:
                return str(run_result)
                
        except Exception as e:
            print(f"Agent search failed: {e}")
            # Fallback to direct search
            return await self._search_products_tool(query)
    
    def _fallback_text_search(self, query: str) -> str:
        """Simple text-based search as fallback."""
        query_words = query.lower().split()
        content_lower = self.catalog_content.lower()
        
        # Find relevant sections
        lines = self.catalog_content.split('\n')
        relevant_lines = []
        
        for line in lines:
            if any(word in line.lower() for word in query_words):
                relevant_lines.append(line.strip())
        
        if relevant_lines:
            result = f"**Found information about '{query}':**\n\n"
            current_section = []
            for line in relevant_lines[:20]:  # Limit results
                if line:
                    current_section.append(line)
            
            result += '\n'.join(current_section)
            result += f"\n\n*Found in catalog: {self.catalog_name}*"
            return result
        else:
            return f"No specific information found for '{query}' in {self.catalog_name}. Try different keywords or browse the catalog overview."