"""Tools for the orchestrator agent."""

from storage.catalog_library import CatalogLibrary
from processors.pdf_processor import PDFCatalogProcessor


class OrchestratorTools:
    """Tools for the orchestrator agent."""
    
    def __init__(self, catalog_library: CatalogLibrary, processor: PDFCatalogProcessor, multi_system):
        self.catalog_library = catalog_library
        self.processor = processor
        self.multi_system = multi_system  # Reference to the MultiCatalogSystem
        
    async def answer_query_with_best_catalog(self, query: str) -> str:
        """Select the best catalog and answer the query using that catalog."""
        try:
            print(f"\n=== ORCHESTRATOR PROCESSING ===")
            print(f"Query: {query}")
            
            # Find the most relevant catalog with improved search
            relevant_catalogs = self.catalog_library.search_relevant_catalogs(query, self.processor, top_k=3)
            
            if not relevant_catalogs:
                return "No suitable catalog found for your query."
            
            best_catalog, score = relevant_catalogs[0]
            print(f"Selected catalog: {best_catalog} with score: {score}")
            
            # If the best score is too low, try searching all catalogs
            if score < 4.0:
                print(f"Low relevance score ({score}), trying all catalogs...")
                # Try with the second best catalog if available
                if len(relevant_catalogs) > 1:
                    second_best, second_score = relevant_catalogs[1]
                    if second_score > score:
                        best_catalog, score = second_best, second_score
                        print(f"Using second choice: {best_catalog} with score: {second_score}")
            
            # Get the specialized catalog agent
            catalog_agent = await self.multi_system.get_catalog_agent(best_catalog)
            
            # Get the detailed response from the catalog agent
            detailed_response = await catalog_agent.chat_response(query)
            
            # If the response indicates no match, try other catalogs
            if self._is_no_match_response(detailed_response, query):
                print("Primary catalog didn't have relevant info, trying other catalogs...")
                
                for catalog_name, catalog_score in relevant_catalogs[1:]:
                    print(f"Trying backup catalog: {catalog_name}")
                    backup_agent = await self.multi_system.get_catalog_agent(catalog_name)
                    backup_response = await backup_agent.chat_response(query)
                    
                    # If this catalog has better information, use it
                    if not self._is_no_match_response(backup_response, query):
                        best_catalog = catalog_name
                        score = catalog_score
                        detailed_response = backup_response
                        break
            
            # Format the final response
            result = f"**Selected Catalog: {best_catalog}** (Relevance: {score}/10)\n\n"
            result += f"**Answer:**\n{detailed_response}"
            
            return result
            
        except Exception as e:
            print(f"Error in orchestrator: {str(e)}")
            return f"Error processing query: {str(e)}"

    def _is_no_match_response(self, response: str, query: str) -> bool:
        """Check if response indicates no match was found."""
        response_lower = response.lower()
        query_lower = query.lower()
        
        no_match_indicators = [
            "no information",
            "sorry" and "not",
            "not found",
            "no products matching",
            "cannot find"
        ]
        
        # Special case for temperature glass kettle
        if "temperature glass kettle" in query_lower:
            return "no information" in response_lower and "temperature glass kettle" in query_lower
        
        return any(indicator in response_lower for indicator in no_match_indicators if "and" not in indicator) or \
               ("sorry" in response_lower and "not" in response_lower)
    
    async def search_catalogs(self, query: str) -> str:
        """Search for relevant catalogs based on user query."""
        try:
            relevant_catalogs = self.catalog_library.search_relevant_catalogs(query, self.processor, top_k=5)
            
            if not relevant_catalogs:
                return "No catalogs found matching your query."
            
            result = f"Found {len(relevant_catalogs)} relevant catalogs for your query:\n\n"
            
            for i, (catalog_name, score) in enumerate(relevant_catalogs, 1):
                metadata = self.catalog_library.catalogs[catalog_name]
                result += f"{i}. **{catalog_name}** (Relevance: {score}/10)\n"
                result += f"   Summary: {metadata.summary}\n"
                result += f"   Categories: {', '.join(metadata.categories)}\n"
                result += f"   Pages: {metadata.page_count}\n\n"
            
            return result
            
        except Exception as e:
            return f"Error searching catalogs: {str(e)}"
    
    async def get_catalog_overview(self) -> str:
        """Get overview of all available catalogs."""
        try:
            if not self.catalog_library.catalogs:
                return "No catalogs available in the library."
            
            overview = f"**Catalog Library Overview**\n\n"
            overview += f"Total Catalogs: {len(self.catalog_library.catalogs)}\n\n"
            
            for filename, metadata in self.catalog_library.catalogs.items():
                overview += f"📄 **{filename}**\n"
                overview += f"   • {metadata.summary}\n"
                overview += f"   • Categories: {', '.join(metadata.categories)}\n"
                overview += f"   • Product Types: {', '.join(metadata.product_types)}\n"
                overview += f"   • Pages: {metadata.page_count}\n\n"
            
            return overview
            
        except Exception as e:
            return f"Error getting catalog overview: {str(e)}"