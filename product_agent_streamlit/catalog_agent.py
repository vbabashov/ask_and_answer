# # # catalog_agent.py
# # import google.generativeai as genai

# # class CatalogAgent:
# #     def __init__(self, catalog_name: str, catalog_content: str, gemini_api_key: str):
# #         self.catalog_name = catalog_name
# #         self.catalog_content = catalog_content
# #         genai.configure(api_key=gemini_api_key)
# #         self.model = genai.GenerativeModel('gemini-1.5-flash')
    
# #     def search_products(self, query: str) -> str:
# #         """Search for products in the catalog content."""
# #         # Limit content size to prevent API issues
# #         content_preview = self.catalog_content[:20000]  # First 20k characters
        
# #         prompt = f"""
# #         Search this catalog for information about: "{query}"
        
# #         Catalog content:
# #         {content_preview}
        
# #         Provide detailed information including:
# #         - Exact product names and model numbers
# #         - Complete specifications and dimensions
# #         - Pricing information if available
# #         - Usage instructions if mentioned
# #         - Warranty details if provided
# #         - Part numbers or SKUs
# #         - Any safety information
        
# #         Be specific and include all relevant details found in the catalog.
# #         If multiple related products are found, list them all.
# #         """
        
# #         try:
# #             response = self.model.generate_content(prompt)
# #             if hasattr(response, 'text') and response.text:
# #                 return response.text
# #             else:
# #                 return self._fallback_text_search(query)
# #         except Exception as e:
# #             print(f"API search failed: {e}")
# #             return self._fallback_text_search(query)
    
# #     def _fallback_text_search(self, query: str) -> str:
# #         """Simple text-based search as fallback."""
# #         query_words = query.lower().split()
# #         content_lower = self.catalog_content.lower()
        
# #         # Find relevant sections
# #         lines = self.catalog_content.split('\n')
# #         relevant_lines = []
        
# #         for line in lines:
# #             if any(word in line.lower() for word in query_words):
# #                 relevant_lines.append(line.strip())
        
# #         if relevant_lines:
# #             # Get surrounding context for better results
# #             result = f"**Found information about '{query}':**\n\n"
            
# #             # Group related lines together
# #             current_section = []
# #             for line in relevant_lines[:20]:  # Limit results
# #                 if line:
# #                     current_section.append(line)
            
# #             result += '\n'.join(current_section)
# #             result += f"\n\n*Found in catalog: {self.catalog_name}*"
# #             return result
# #         else:
# #             return f"No specific information found for '{query}' in {self.catalog_name}. Try different keywords or browse the catalog overview."

# import agents
# from agents import function_tool
# from catalog_manager import CatalogManager

# class CatalogAgent:
#     def __init__(self, catalog_name: str, catalog_content: str, gemini_api_key: str, async_openai_client):
#         self.catalog_name = catalog_name
#         self.catalog_content = catalog_content
#         self.async_openai_client = async_openai_client

#         # Define tools for the agent
#         self.tools = [
#             function_tool(self.search_products),
#             function_tool(self.get_catalog_overview),
#         ]

#         # Initialize the agent
#         self.agent = agents.Agent(
#             name=f"Catalog Agent - {self.catalog_name}",
#             instructions=f"""
#             You are an expert catalog agent for the catalog: {self.catalog_name}.
#             Use the tools provided to search for products and provide detailed information.
#             Always base your responses on the actual catalog content.
#             """,
#             tools=self.tools,
#             model=agents.OpenAIChatCompletionsModel(
#                 model="gemini-2.5-flash",
#                 openai_client=self.async_openai_client,
#             ),
#         )

#     async def search_products(self, query: str) -> str:
#         """Search for products in the catalog content."""
#         content_preview = self.catalog_content[:20000]  # Limit content size
#         prompt = f"""
#         Search this catalog for information about: "{query}"

#         Catalog content:
#         {content_preview}

#         Provide detailed information including:
#         - Exact product names and model numbers
#         - Complete specifications and dimensions
#         - Pricing information if available
#         - Usage instructions if mentioned
#         - Warranty details if provided
#         - Part numbers or SKUs
#         - Any safety information

#         Be specific and include all relevant details found in the catalog.
#         """
#         return prompt

#     async def get_catalog_overview(self) -> str:
#         """Provide an overview of the catalog."""
#         prompt = f"""
#         Provide a concise overview of the catalog: {self.catalog_name}.

#         Catalog content:
#         {self.catalog_content[:20000]}

#         Include:
#         - Main product categories
#         - Approximate number of products
#         - Key brands and manufacturers
#         - Unique features or specializations
#         """
#         return prompt


# catalog_agent.py
import asyncio
from agents import Agent, OpenAIChatCompletionsModel, function_tool

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
                model="gpt-4o-mini",  # Use a valid OpenAI model
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
            response = await self.agent.run(f"Search for information about: {query}")
            return response.content if hasattr(response, 'content') else str(response)
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