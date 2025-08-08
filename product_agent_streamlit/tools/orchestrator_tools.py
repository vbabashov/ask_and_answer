"""
Tools for the orchestrator agent
"""

from storage.catalog_library import CatalogLibrary
from processors.pdf_processor import PDFCatalogProcessor

class OrchestratorTools:
    """Tools for the orchestrator agent."""
    
    def __init__(self, catalog_library: CatalogLibrary, processor: PDFCatalogProcessor, multi_system):
        self.catalog_library = catalog_library
        self.processor = processor
        self.multi_system = multi_system  # Reference to the MultiCatalogSystem
        
    async def answer_query_with_best_catalog(self, query: str) -> str:
        """Enhanced query processing with deep catalog content extraction."""
        try:
            print(f"\n=== DEEP ORCHESTRATOR PROCESSING ===")
            print(f"Query: {query}")
            
            # Truncate query if too long to avoid API issues
            if len(query) > 1000:
                query = query[:1000] + "..."
                print(f"Query truncated to avoid API limits")
            
            # Get ranked catalogs
            relevant_catalogs = self.catalog_library.search_relevant_catalogs(query, self.processor, top_k=3)
            
            if not relevant_catalogs:
                return "❌ No catalogs available to search."
            
            best_catalog, score = relevant_catalogs[0]
            print(f"✅ Selected catalog: {best_catalog} (score: {score})")
            
            # Get the catalog agent
            catalog_agent = await self.multi_system.get_catalog_agent(best_catalog)
            
            # Try multiple approaches with fallbacks
            detailed_response = None
            
            # Approach 1: Direct extraction with simplified query
            if hasattr(catalog_agent, 'tools') and catalog_agent.tools:
                print(f"🔍 Trying direct extraction...")
                try:
                    detailed_response = await catalog_agent.tools.search_products(query)
                    if len(detailed_response) > 200 and "No direct matches" not in detailed_response:
                        print(f"✅ Direct extraction successful: {len(detailed_response)} chars")
                    else:
                        detailed_response = None
                except Exception as e:
                    print(f"Direct extraction failed: {e}")
                    detailed_response = None
            
            # Approach 2: Try agent chat if direct extraction failed
            if not detailed_response:
                print(f"🔍 Trying agent chat response...")
                try:
                    detailed_response = await catalog_agent.chat_response(query)
                    if len(detailed_response) > 100:
                        print(f"✅ Agent chat successful: {len(detailed_response)} chars")
                except Exception as e:
                    print(f"Agent chat failed: {e}")
                    detailed_response = f"Error processing query in {best_catalog}: {str(e)}"
            
            # Approach 3: Fallback to other catalogs if needed
            if not detailed_response or len(detailed_response) < 100:
                print("Trying backup catalogs...")
                for backup_catalog, backup_score in relevant_catalogs[1:]:
                    try:
                        backup_agent = await self.multi_system.get_catalog_agent(backup_catalog)
                        if hasattr(backup_agent, 'tools') and backup_agent.tools:
                            backup_response = await backup_agent.tools.search_products(query)
                            if len(backup_response) > 200 and "No direct matches" not in backup_response:
                                best_catalog = backup_catalog
                                score = backup_score
                                detailed_response = backup_response
                                print(f"✅ Backup catalog {backup_catalog} provided good response")
                                break
                    except Exception as e:
                        print(f"Backup catalog {backup_catalog} failed: {e}")
                        continue
            
            # Final fallback
            if not detailed_response or len(detailed_response.strip()) < 50:
                detailed_response = f"I found relevant catalog '{best_catalog}' but encountered issues extracting detailed information. Please try rephrasing your question or ask about specific product features."
            
            # Format the final response
            result = f"**Selected Catalog: {best_catalog}** (Relevance: {score:.1f}/10)\n\n"
            result += detailed_response

            return result
            
        except Exception as e:
            print(f"Error in deep orchestrator processing: {str(e)}")
            return f"❌ Error processing query: {str(e)}"
    
    def _validate_response_quality(self, response: str, query: str) -> bool:
        """Check if response contains actual detailed information."""
        response_lower = response.lower()
        query_lower = query.lower()
        
        # Good indicators
        good_indicators = [
            "specifications", "features", "model", "instructions", 
            "steps", "warranty", "price", "$", "dimensions",
            "includes", "operation", "safety", "cleaning"
        ]
        
        # Bad indicators
        bad_indicators = [
            "catalog contains", "summary", "overview of", 
            "information about", "details about", "this manual"
        ]
        
        has_good = any(indicator in response_lower for indicator in good_indicators)
        has_bad = any(indicator in response_lower for indicator in bad_indicators)
        is_substantial = len(response.strip()) > 200
        
        return has_good and not has_bad and is_substantial
    
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

    async def get_detailed_catalog_summary(self) -> str:
        """Get detailed summary of all catalogs with their specializations."""
        try:
            if not self.catalog_library.catalogs:
                return "📚 **No catalogs available in the library.**"
            
            summary = f"📚 **Comprehensive Catalog Library Analysis**\n\n"
            summary += f"**Total Catalogs:** {len(self.catalog_library.catalogs)}\n\n"
            
            # Group catalogs by category for better organization
            categories = {}
            for filename, metadata in self.catalog_library.catalogs.items():
                for category in metadata.categories:
                    if category not in categories:
                        categories[category] = []
                    categories[category].append((filename, metadata))
            
            summary += "**📋 Catalogs by Category:**\n\n"
            
            for category, catalogs in categories.items():
                summary += f"### 🏷️ {category}\n"
                for filename, metadata in catalogs:
                    summary += f"**• {filename}**\n"
                    summary += f"  - Summary: {metadata.summary}\n"
                    summary += f"  - Products: {', '.join(metadata.product_types[:3])}\n"
                    summary += f"  - Brands: {', '.join(metadata.brand_names[:2]) if metadata.brand_names else 'Generic'}\n"
                    summary += f"  - Pages: {metadata.page_count}\n\n"
            
            summary += "\n**💡 Search Strategy:**\n"
            summary += "• Ask specific product questions for detailed extraction\n"
            summary += "• The system will automatically select the most relevant catalog\n"
            summary += "• Deep content analysis will provide comprehensive answers\n"
            
            return summary
            
        except Exception as e:
            return f"Error generating catalog summary: {str(e)}"