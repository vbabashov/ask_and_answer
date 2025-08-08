# # orchestrator_agent.py
# import google.generativeai as genai
# from catalog_manager import CatalogManager

# class OrchestratorAgent:
#     def __init__(self, gemini_api_key: str, catalog_manager: CatalogManager):
#         genai.configure(api_key=gemini_api_key)
#         self.model = genai.GenerativeModel('gemini-1.5-flash')
#         self.catalog_manager = catalog_manager
    
#     def select_best_catalog(self, query: str) -> str:
#         """Select the most relevant catalog for the query."""
#         if not self.catalog_manager.catalogs:
#             return None
        
#         if len(self.catalog_manager.catalogs) == 1:
#             return list(self.catalog_manager.catalogs.keys())[0]
        
#         # Create catalog options text
#         catalog_options = ""
#         for i, (filename, info) in enumerate(self.catalog_manager.catalogs.items(), 1):
#             catalog_options += f"{i}. **{filename}**: {info.summary}\n"
        
#         prompt = f"""
#         Select the most relevant catalog for this query: "{query}"
        
#         Available catalogs:
#         {catalog_options}
        
#         Respond with ONLY the catalog filename (including .pdf extension) that best matches the query.
#         Consider product types, categories, and specializations mentioned in the summaries.
#         """
        
#         try:
#             response = self.model.generate_content(prompt)
#             if hasattr(response, 'text') and response.text:
#                 selected = response.text.strip()
                
#                 # Find matching catalog name
#                 for catalog_name in self.catalog_manager.catalogs.keys():
#                     if catalog_name.lower() in selected.lower() or selected.lower() in catalog_name.lower():
#                         return catalog_name
                
#                 # Fallback: return first catalog
#                 return list(self.catalog_manager.catalogs.keys())[0]
            
#         except Exception as e:
#             print(f"Error in catalog selection: {e}")
        
#         # Fallback: return first available catalog
#         return list(self.catalog_manager.catalogs.keys())[0]

import agents
from agents import function_tool
from catalog_manager import CatalogManager

class OrchestratorAgent:
    def __init__(self, gemini_api_key: str, catalog_manager: CatalogManager, async_openai_client):
        self.catalog_manager = catalog_manager
        self.async_openai_client = async_openai_client

        # Define tools for the agent
        self.tools = [
            function_tool(self.select_best_catalog),
        ]

        # Initialize the agent
        self.agent = agents.Agent(
            name="Orchestrator Agent",
            instructions="""
            You are an orchestrator agent responsible for selecting the most relevant catalog
            for a given query. Use the tools provided to analyze the query and choose the best catalog.
            """,
            tools=self.tools,
            model=agents.OpenAIChatCompletionsModel(
                model="gemini-2.5-flash",
                openai_client=self.async_openai_client,
            ),
        )

    async def select_best_catalog(self, query: str) -> str:
        """Select the most relevant catalog for the query."""
        if not self.catalog_manager.catalogs:
            return "No catalogs available."

        if len(self.catalog_manager.catalogs) == 1:
            return list(self.catalog_manager.catalogs.keys())[0]

        # Create catalog options text
        catalog_options = ""
        for i, (filename, info) in enumerate(self.catalog_manager.catalogs.items(), 1):
            catalog_options += f"{i}. **{filename}**: {info.summary}\n"

        prompt = f"""
        Select the most relevant catalog for this query: "{query}"

        Available catalogs:
        {catalog_options}

        Respond with ONLY the catalog filename (including .pdf extension) that best matches the query.
        Consider product types, categories, and specializations mentioned in the summaries.
        """
        return prompt