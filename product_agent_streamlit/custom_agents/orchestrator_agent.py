# orchestrator_agent.py
from agents import Agent, OpenAIChatCompletionsModel, function_tool, Runner
from processors.catalog_manager import CatalogManager

class OrchestratorAgent:
    def __init__(self, gemini_api_key: str, catalog_manager: CatalogManager, async_openai_client):
        self.catalog_manager = catalog_manager
        self.async_openai_client = async_openai_client
        self.tools = [
            function_tool(self._search_best_catalog),  # Reference the new method here
        ]
        # Initialize the agent
        self.agent = Agent(
            name="Orchestrator Agent",
            instructions="""
            You are an orchestrator agent responsible for selecting the most relevant catalog
            for a given query. When given a query and a list of available catalogs with their summaries,
            you must respond with ONLY the exact catalog filename (including .pdf extension) that best 
            matches the query. Do not provide explanations, just the filename.
            """,
            model=OpenAIChatCompletionsModel(
                model="gemini-2.5-flash",  # Use valid OpenAI model
                openai_client=self.async_openai_client,
            ),
            tools=self.tools,
        )

    async def _search_best_catalog(self, query: str) -> str:
        """Tool function to search for the best catalog based on the query."""
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

    async def select_best_catalog(self, query: str) -> str:
        """Select the most relevant catalog for the query."""
        if not self.catalog_manager.catalogs:
            return None

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
        
        try:
            response = await Runner.run(self.agent, input=prompt)  # Correct method to run the agent
            selected = response.content if hasattr(response, 'content') else str(response)
            selected = selected.strip()
            
            # Find matching catalog name
            for catalog_name in self.catalog_manager.catalogs.keys():
                if catalog_name.lower() in selected.lower() or selected.lower() in catalog_name.lower():
                    return catalog_name
            
            # Fallback: return first catalog
            return list(self.catalog_manager.catalogs.keys())[0]
            
        except Exception as e:
            print(f"Error in catalog selection: {e}")
            # Fallback: return first available catalog
            return list(self.catalog_manager.catalogs.keys())[0]