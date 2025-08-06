# import asyncio
# from typing import Dict, List, Optional, Tuple
# import logging
# import json

# from services.catalog_service import CatalogService
# from services.gemini_service import GeminiService
# from utils import pdf_to_images

# logger = logging.getLogger(__name__)

# class SummaryAgent:
#     """Agent responsible for creating detailed catalog summaries"""
    
#     def __init__(self, gemini_service: GeminiService):
#         self.gemini_service = gemini_service
    
#     async def create_detailed_summary(self, pdf_path: str, catalog_name: str) -> Dict[str, any]:
#         """Create a comprehensive summary of the catalog"""
#         logger.info(f"Creating detailed summary for: {catalog_name}")
        
#         # Convert PDF to images
#         images = pdf_to_images(pdf_path)
        
#         # Analyze in batches for better performance
#         batch_size = 5
#         all_content = []
        
#         for i in range(0, len(images), batch_size):
#             batch = images[i:i + batch_size]
#             content = await self._analyze_batch(batch, i, catalog_name)
#             all_content.append(content)
        
#         # Create consolidated summary
#         full_content = "\n\n".join(all_content)
#         summary = await self._consolidate_summary(full_content, catalog_name)
        
#         return summary
    
#     async def _analyze_batch(self, images: List, batch_start: int, catalog_name: str) -> str:
#         """Analyze a batch of images for detailed content extraction"""
#         prompt = f"""
#         You are analyzing pages {batch_start + 1} to {batch_start + len(images)} of catalog "{catalog_name}".
        
#         Extract EVERYTHING visible including:
        
#         PRODUCTS:
#         - Exact product names, model numbers, SKUs
#         - Product categories and subcategories  
#         - Brand names and manufacturers
#         - Detailed descriptions and features
#         - Technical specifications
#         - Prices and variations
#         - Colors, sizes, materials
        
#         CATALOG STRUCTURE:
#         - Section headers and categories
#         - Page numbers and organization
#         - Company information
#         - Contact details
        
#         Be extremely thorough. Extract ALL text including small print, captions, and product variations.
#         Focus on creating searchable content that captures every product detail.
        
#         Format as structured text with clear product listings.
#         """
        
#         try:
#             response = self.gemini_service.model.generate_content([prompt] + images)
#             return response.text
#         except Exception as e:
#             logger.error(f"Error analyzing batch {batch_start}: {e}")
#             return f"Error analyzing batch {batch_start}: {e}"
    
#     async def _consolidate_summary(self, full_content: str, catalog_name: str) -> Dict[str, any]:
#         """Consolidate all content into a structured summary"""
#         prompt = f"""
#         Create a comprehensive, searchable summary for catalog "{catalog_name}".
        
#         Based on this extracted content:
#         {full_content[:15000]}
        
#         Provide a JSON response with:
#         {{
#             "detailed_summary": "Comprehensive 4-5 sentence summary covering ALL product types, brands, and specializations",
#             "product_categories": ["specific_category1", "specific_category2", ...],
#             "all_products": ["exact_product_name1", "exact_product_name2", ...],
#             "brands": ["brand1", "brand2", ...],
#             "product_types": ["specific_type1", "specific_type2", ...],
#             "key_features": ["feature1", "feature2", ...],
#             "price_ranges": ["range1", "range2", ...],
#             "target_market": "description of target customers",
#             "specializations": ["specialization1", "specialization2", ...],
#             "searchable_keywords": ["keyword1", "keyword2", "keyword3", ...]
#         }}
        
#         CRITICAL: Be extremely specific. Include ALL product names and variations found.
#         Make the summary highly searchable for any product query.
        
#         Return only valid JSON.
#         """
        
#         try:
#             response = self.gemini_service.model.generate_content(prompt)
#             response_text = response.text.strip()
            
#             # Clean JSON response
#             if response_text.startswith('```json'):
#                 response_text = response_text[7:-3]
#             elif response_text.startswith('```'):
#                 response_text = response_text[3:-3]
                
#             return json.loads(response_text)
            
#         except Exception as e:
#             logger.error(f"Error consolidating summary: {e}")
#             return {
#                 "detailed_summary": f"Product catalog: {catalog_name}",
#                 "product_categories": ["general"],
#                 "all_products": [],
#                 "brands": [],
#                 "product_types": ["products"],
#                 "key_features": [],
#                 "price_ranges": [],
#                 "target_market": "general consumers",
#                 "specializations": [],
#                 "searchable_keywords": [catalog_name.lower()]
#             }

# class RelevanceAgent:
#     """Agent responsible for scoring catalog relevance to queries"""
    
#     def __init__(self, gemini_service: GeminiService):
#         self.gemini_service = gemini_service
    
#     async def score_catalogs(self, query: str, catalog_summaries: Dict[str, Dict]) -> List[Tuple[str, float, str]]:
#         """Score all catalogs for relevance to the query"""
        
#         # Format summaries for scoring
#         formatted_summaries = self._format_summaries_for_scoring(catalog_summaries)
        
#         prompt = f"""
#         USER QUERY: "{query}"
        
#         AVAILABLE CATALOGS:
#         {formatted_summaries}
        
#         TASK: Score each catalog for relevance to the user query using this detailed scoring system:
        
#         SCORING CRITERIA (0-10):
#         10: Exact product match - catalog contains the specific product mentioned
#         9: Very close match - similar/related products in same category
#         8: Good category match - products in related category
#         7: Moderate relevance - some connection to query
#         5-6: Low relevance - minimal connection
#         1-4: Poor match - barely related
#         0: No match - completely unrelated
        
#         ANALYZE:
#         - Exact product name matches
#         - Category/type matches  
#         - Brand matches
#         - Feature/specification matches
#         - Use case matches
        
#         Return ONLY a JSON array:
#         [
#             {{"catalog": "exact_filename.pdf", "score": 9.5, "reason": "Contains multiple fan models including tower fans and desk fans"}},
#             {{"catalog": "filename2.pdf", "score": 2.0, "reason": "Only contains kitchen appliances, no fans"}}
#         ]
        
#         Include ALL catalogs. Be precise with scoring.
#         """
        
#         try:
#             response = self.gemini_service.model.generate_content(prompt)
#             response_text = response.text.strip()
            
#             # Clean response
#             if response_text.startswith('```json'):
#                 response_text = response_text[7:-3]
#             elif response_text.startswith('```'):
#                 response_text = response_text[3:-3]
            
#             scores = json.loads(response_text)
            
#             # Convert to desired format
#             results = []
#             for item in scores:
#                 catalog_name = item.get('catalog', '')
#                 score = float(item.get('score', 0))
#                 reason = item.get('reason', 'No reason provided')
#                 results.append((catalog_name, score, reason))
            
#             # Sort by score descending
#             results.sort(key=lambda x: x[1], reverse=True)
#             return results
            
#         except Exception as e:
#             logger.error(f"Error scoring catalogs: {e}")
#             # Fallback: return all catalogs with neutral scores
#             return [(name, 5.0, "Fallback scoring") for name in catalog_summaries.keys()]
    
#     def _format_summaries_for_scoring(self, catalog_summaries: Dict[str, Dict]) -> str:
#         """Format catalog summaries for relevance scoring"""
#         formatted = []
        
#         for filename, summary_data in catalog_summaries.items():
#             entry = f"""
# CATALOG: {filename}
# Summary: {summary_data.get('detailed_summary', 'No summary')}
# Products: {', '.join(summary_data.get('all_products', [])[:10])}
# Categories: {', '.join(summary_data.get('product_categories', []))}
# Brands: {', '.join(summary_data.get('brands', []))}
# Product Types: {', '.join(summary_data.get('product_types', []))}
# Keywords: {', '.join(summary_data.get('searchable_keywords', [])[:15])}
#             """.strip()
#             formatted.append(entry)
        
#         return "\n\n".join(formatted)

# class DetailedCatalogAgent:
#     """Agent responsible for detailed product searches within a specific catalog"""
    
#     def __init__(self, catalog_name: str, gemini_service: GeminiService):
#         self.catalog_name = catalog_name
#         self.gemini_service = gemini_service
#         self.catalog_content = ""
#         self.is_initialized = False
    
#     async def initialize(self, pdf_path: str) -> None:
#         """Initialize agent with detailed catalog content"""
#         if self.is_initialized:
#             return
            
#         logger.info(f"Initializing detailed agent for: {self.catalog_name}")
        
#         # Convert PDF to images
#         images = pdf_to_images(pdf_path)
        
#         # Extract detailed content in batches
#         batch_size = 8
#         all_content = []
        
#         for i in range(0, len(images), batch_size):
#             batch = images[i:i + batch_size]
#             content = await self._extract_detailed_content(batch, i)
#             all_content.append(content)
        
#         # Consolidate all content
#         full_content = "\n\n".join(all_content)
#         self.catalog_content = await self._create_searchable_database(full_content)
#         self.is_initialized = True
        
#         logger.info(f"Detailed agent initialized: {self.catalog_name}")
    
#     async def _extract_detailed_content(self, images: List, batch_start: int) -> str:
#         """Extract comprehensive content from image batch"""
#         prompt = f"""
#         Extract ALL content from pages {batch_start + 1} to {batch_start + len(images)} of "{self.catalog_name}".
        
#         EXTRACT EVERYTHING:
#         - Every product name, model number, SKU, variation
#         - Complete descriptions and specifications
#         - All prices, dimensions, weights, materials
#         - Features, capabilities, usage instructions
#         - Brand information and contact details
#         - Warranty information
#         - Installation/setup details
#         - Compatibility information
#         - Technical diagrams descriptions
#         - Part numbers and accessories
#         - Safety information
#         - ALL visible text including fine print
        
#         ORGANIZATION:
#         - Group by product/section
#         - Include page references
#         - Maintain logical structure
#         - Create searchable format
        
#         Be exhaustive. Don't skip any text or details.
#         """
        
#         try:
#             response = self.gemini_service.model.generate_content([prompt] + images)
#             return response.text
#         except Exception as e:
#             logger.error(f"Error extracting content from batch {batch_start}: {e}")
#             return f"Error in batch {batch_start}: {e}"
    
#     async def _create_searchable_database(self, full_content: str) -> str:
#         """Create a searchable database from all extracted content"""
#         prompt = f"""
#         Create a comprehensive, searchable database for "{self.catalog_name}".
        
#         Source content:
#         {full_content[:20000]}
        
#         Format as:
        
#         === COMPLETE PRODUCT INDEX ===
#         [Alphabetical list of ALL products with page numbers]
        
#         === PRODUCT CATEGORIES ===
#         [Organize products by category]
        
#         === DETAILED PRODUCT DATABASE ===
#         [For each product: name, model, features, specs, price, page]
        
#         === BRAND AND MANUFACTURER INFO ===
#         [All brand information and contact details]
        
#         === TECHNICAL SPECIFICATIONS ===
#         [All technical details organized by product]
        
#         === SEARCH KEYWORDS ===
#         [Comprehensive keyword list for search optimization]
        
#         Make this extremely searchable and comprehensive.
#         Include every product detail found in the catalog.
#         """
        
#         try:
#             response = self.gemini_service.model.generate_content(prompt)
#             return response.text
#         except Exception as e:
#             logger.error(f"Error creating searchable database: {e}")
#             return full_content[:20000]  # Fallback
    
#     async def search_products(self, query: str) -> str:
#         """Search for products matching the query"""
#         if not self.is_initialized:
#             return "Agent not initialized"
        
#         prompt = f"""
#         SEARCH TASK: Find information about "{query}" in catalog "{self.catalog_name}"
        
#         Catalog Database:
#         {self.catalog_content[:15000]}
        
#         SEARCH INSTRUCTIONS:
#         1. Look for EXACT matches to "{query}"
#         2. Look for similar/related products
#         3. Check product names, descriptions, categories, features
#         4. Include model numbers, specifications, prices
#         5. Provide page numbers where found
        
#         RESPONSE FORMAT:
#         If products found:
#         - List all matching products with full details
#         - Include exact names, models, specifications
#         - Show prices and key features  
#         - Mention page numbers
#         - Explain why each product matches
        
#         If no exact matches:
#         - State "No exact matches for '{query}' found"
#         - Suggest similar/related products if available
#         - List main product categories in this catalog
        
#         Be thorough and accurate. Don't invent information.
#         """
        
#         try:
#             response = self.gemini_service.model.generate_content(prompt)
#             return response.text
#         except Exception as e:
#             logger.error(f"Search error in {self.catalog_name}: {e}")
#             return f"Error searching {self.catalog_name}: {e}"

# class ImprovedOrchestrator:
#     """Improved orchestrator that uses specialized agents"""
    
#     def __init__(self, catalog_service: CatalogService, gemini_service: GeminiService):
#         self.catalog_service = catalog_service
#         self.gemini_service = gemini_service
#         self.summary_agent = SummaryAgent(gemini_service)
#         self.relevance_agent = RelevanceAgent(gemini_service)
#         self.detailed_agents: Dict[str, DetailedCatalogAgent] = {}
#         self.catalog_summaries: Dict[str, Dict] = {}
    
#     async def initialize_catalog(self, catalog_name: str, pdf_path: str) -> None:
#         """Initialize a catalog with detailed summary"""
#         logger.info(f"Initializing catalog: {catalog_name}")
        
#         # Create detailed summary
#         summary = await self.summary_agent.create_detailed_summary(pdf_path, catalog_name)
#         self.catalog_summaries[catalog_name] = summary
        
#         logger.info(f"Catalog summary created: {catalog_name}")
    
#     async def process_query(self, query: str) -> Tuple[str, Optional[str]]:
#         """Process query using improved agent system"""
#         try:
#             logger.info(f"Processing query with improved system: {query}")
            
#             if not self.catalog_summaries:
#                 return "No catalogs available for search.", None
            
#             # Score all catalogs for relevance
#             scores = await self.relevance_agent.score_catalogs(query, self.catalog_summaries)
            
#             if not scores:
#                 return "Error scoring catalogs for relevance.", None
            
#             logger.info(f"Top catalog scores: {scores[:3]}")
            
#             # Get best catalog
#             best_catalog, best_score, reason = scores[0]
            
#             if best_score < 1.0:
#                 return f"No relevant catalogs found for '{query}'. Available catalogs focus on: {self._get_available_categories()}", None
            
#             # Get detailed agent for best catalog
#             detailed_agent = await self._get_detailed_agent(best_catalog)
            
#             # Search for detailed information
#             detailed_response = await detailed_agent.search_products(query)
            
#             # Try backup catalogs if response is poor
#             if self._is_poor_response(detailed_response) and len(scores) > 1:
#                 for backup_catalog, backup_score, backup_reason in scores[1:3]:
#                     if backup_score >= 3.0:
#                         backup_agent = await self._get_detailed_agent(backup_catalog)
#                         backup_response = await backup_agent.search_products(query)
                        
#                         if not self._is_poor_response(backup_response):
#                             best_catalog = backup_catalog
#                             best_score = backup_score
#                             detailed_response = backup_response
#                             reason = backup_reason
#                             break
            
#             # Format final response
#             response = f"**🎯 Selected Catalog: {best_catalog}**\n"
#             response += f"**📊 Relevance Score: {best_score:.1f}/10**\n"
#             response += f"**💡 Selection Reason:** {reason}\n\n"
#             response += f"**📋 Search Results:**\n{detailed_response}"
            
#             return response, best_catalog
            
#         except Exception as e:
#             logger.error(f"Error in improved orchestrator: {e}")
#             return f"Error processing query: {e}", None
    
#     async def _get_detailed_agent(self, catalog_name: str) -> DetailedCatalogAgent:
#         """Get or create detailed agent for catalog"""
#         if catalog_name not in self.detailed_agents:
#             # Get catalog metadata
#             metadata = self.catalog_service.get_catalog_by_name(catalog_name)
#             if not metadata:
#                 raise ValueError(f"Catalog {catalog_name} not found")
            
#             # Create and initialize detailed agent
#             agent = DetailedCatalogAgent(catalog_name, self.gemini_service)
#             await agent.initialize(metadata.file_path)
            
#             self.detailed_agents[catalog_name] = agent
        
#         return self.detailed_agents[catalog_name]
    
#     def _is_poor_response(self, response: str) -> bool:
#         """Check if response indicates poor results"""
#         poor_indicators = [
#             "no exact matches", "no products matching", "not found",
#             "sorry", "unable to find", "no information", "no relevant"
#         ]
#         return any(indicator in response.lower() for indicator in poor_indicators)
    
#     def _get_available_categories(self) -> str:
#         """Get summary of available catalog categories"""
#         categories = set()
#         for summary in self.catalog_summaries.values():
#             categories.update(summary.get('product_categories', []))
#         return ', '.join(list(categories)[:5])

# # Add this method to ImprovedAgentService class in improved_agent_service.py

# class ImprovedAgentService:
#     """Improved agent service using specialized agents"""
    
#     def __init__(self, catalog_service: CatalogService, gemini_service: GeminiService):
#         self.catalog_service = catalog_service
#         self.gemini_service = gemini_service
#         self.orchestrator = ImprovedOrchestrator(catalog_service, gemini_service)
    
#     async def initialize_catalog(self, catalog_name: str, pdf_path: str) -> None:
#         """Initialize a new catalog in the system"""
#         logger.info(f"ImprovedAgentService: Initializing catalog {catalog_name}")
#         await self.orchestrator.initialize_catalog(catalog_name, pdf_path)
#         logger.info(f"ImprovedAgentService: Completed initialization for {catalog_name}")
    
#     async def process_query(self, query: str) -> str:
#         """Process query using improved orchestrator"""
#         # Check if we have any catalogs
#         if self.get_summary_count() == 0:
#             return "No catalogs have been processed yet. Please upload PDF catalogs and wait for processing to complete."
        
#         response, _ = await self.orchestrator.process_query(query)
#         return response
    
#     def get_agent_count(self) -> int:
#         """Get number of active detailed agents"""
#         return len(self.orchestrator.detailed_agents)
    
#     def get_summary_count(self) -> int:
#         """Get number of catalog summaries"""
#         return len(self.orchestrator.catalog_summaries)
# File: services/optimized_agent_service.py
import asyncio
from typing import Dict, List, Optional, Tuple
import logging
import json

from services.catalog_service import CatalogService
from services.gemini_service import GeminiService
from utils import pdf_to_images

logger = logging.getLogger(__name__)

class UnifiedCatalogAgent:
    """Single agent that handles all catalog operations efficiently"""
    
    def __init__(self, catalog_name: str, gemini_service: GeminiService):
        self.catalog_name = catalog_name
        self.gemini_service = gemini_service
        
        # All data stored in single initialization
        self.catalog_summary = {}
        self.detailed_content = ""
        self.product_index = {}
        self.is_initialized = False
    
    async def initialize_complete_catalog(self, pdf_path: str) -> None:
        """Single comprehensive initialization that extracts everything needed"""
        if self.is_initialized:
            return
            
        logger.info(f"Starting unified initialization for: {self.catalog_name}")
        
        # Convert PDF to images once
        images = pdf_to_images(pdf_path)
        
        # Process all pages in optimized batches
        batch_size = 8  # Increased batch size for efficiency
        all_extracted_data = []
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            batch_data = await self._extract_complete_batch_data(batch, i)
            all_extracted_data.append(batch_data)
        
        # Combine all extracted data
        combined_data = "\n\n=== BATCH SEPARATOR ===\n\n".join(all_extracted_data)
        
        # Single comprehensive analysis to create both summary and detailed content
        catalog_analysis = await self._create_unified_catalog_analysis(combined_data)
        
        # Parse the unified analysis
        self._parse_unified_analysis(catalog_analysis)
        
        self.is_initialized = True
        logger.info(f"Unified initialization complete for: {self.catalog_name}")
    
    async def _extract_complete_batch_data(self, images: List, batch_start: int) -> str:
        """Extract all necessary data in a single comprehensive pass"""
        prompt = f"""
        COMPREHENSIVE EXTRACTION for pages {batch_start + 1} to {batch_start + len(images)} of "{self.catalog_name}":
        
        Extract EVERYTHING for both summary creation AND detailed search:
        
        PRODUCTS (for both summary and search):
        - Complete product names, models, SKUs, variations
        - All specifications, features, capabilities
        - Prices, dimensions, weights, materials
        - Brand information and manufacturers
        - Product categories and subcategories
        - Technical specifications and compatibility
        
        ORGANIZATIONAL DATA:
        - Section headers and page structure
        - Contact information and company details
        - Warranty and support information
        - Installation/setup instructions
        
        SEARCH OPTIMIZATION:
        - Extract ALL searchable terms and keywords
        - Include synonyms and variations
        - Note relationships between products
        - Capture all descriptive text
        
        FORMAT: Create structured, comprehensive content that can be used for:
        1. Creating catalog summaries and metadata
        2. Relevance scoring and catalog selection  
        3. Detailed product searches and responses
        
        Be extremely thorough - this is the ONLY extraction pass.
        """
        
        try:
            response = self.gemini_service.model.generate_content([prompt] + images)
            return response.text
        except Exception as e:
            logger.error(f"Error in unified extraction for batch {batch_start}: {e}")
            return f"Error in batch {batch_start}: {e}"
    
    async def _create_unified_catalog_analysis(self, combined_data: str) -> str:
        """Create comprehensive analysis that serves all purposes"""
        prompt = f"""
        Create a UNIFIED ANALYSIS for catalog "{self.catalog_name}" that serves multiple purposes:
        
        Source data:
        {combined_data[:25000]}
        
        Create analysis with these sections:
        
        === CATALOG SUMMARY FOR SCORING ===
        {{
            "detailed_summary": "Comprehensive 4-5 sentence summary with ALL product types and brands",
            "product_categories": ["specific_category1", "category2", ...],
            "all_products": ["exact_product_name1", "product2", ...],
            "brands": ["brand1", "brand2", ...],
            "product_types": ["specific_type1", "type2", ...],
            "key_features": ["feature1", "feature2", ...],
            "searchable_keywords": ["keyword1", "keyword2", "keyword3", ...]
        }}
        
        === DETAILED PRODUCT DATABASE ===
        [Comprehensive, searchable product database organized by:
        - Product categories
        - Complete product listings with all details
        - Specifications, prices, features
        - Page references
        - Technical information
        - Cross-references and related products]
        
        === SEARCH OPTIMIZATION INDEX ===
        [Keyword mapping and search terms for quick product location]
        
        CRITICAL: Make this analysis comprehensive enough that no further PDF processing is needed.
        This will be used for catalog scoring, selection, and detailed product searches.
        """
        
        try:
            response = self.gemini_service.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error creating unified analysis: {e}")
            return combined_data[:25000]  # Fallback
    
    def _parse_unified_analysis(self, analysis: str) -> None:
        """Parse the unified analysis into summary and detailed content"""
        try:
            # Extract JSON summary
            summary_start = analysis.find('{')
            summary_end = analysis.find('}', summary_start) + 1
            
            if summary_start != -1 and summary_end > summary_start:
                summary_json = analysis[summary_start:summary_end]
                self.catalog_summary = json.loads(summary_json)
            else:
                # Fallback summary
                self.catalog_summary = {
                    "detailed_summary": f"Product catalog: {self.catalog_name}",
                    "product_categories": ["general"],
                    "all_products": [],
                    "brands": [],
                    "product_types": ["products"],
                    "key_features": [],
                    "searchable_keywords": [self.catalog_name.lower()]
                }
            
            # Store detailed content
            detailed_start = analysis.find("=== DETAILED PRODUCT DATABASE ===")
            if detailed_start != -1:
                self.detailed_content = analysis[detailed_start:]
            else:
                self.detailed_content = analysis
                
        except Exception as e:
            logger.error(f"Error parsing unified analysis: {e}")
            # Set fallback values
            self.catalog_summary = {
                "detailed_summary": f"Product catalog: {self.catalog_name}",
                "product_categories": ["general"],
                "all_products": [],
                "brands": [],
                "product_types": ["products"],
                "key_features": [],
                "searchable_keywords": [self.catalog_name.lower()]
            }
            self.detailed_content = analysis
    
    def get_summary_data(self) -> Dict:
        """Get summary data for relevance scoring"""
        return self.catalog_summary
    
    async def search_products(self, query: str) -> str:
        """Search products using pre-processed detailed content"""
        if not self.is_initialized:
            return "Catalog not initialized"
        
        prompt = f"""
        SEARCH QUERY: "{query}" in catalog "{self.catalog_name}"
        
        Pre-processed Catalog Database:
        {self.detailed_content[:15000]}
        
        SEARCH TASK:
        1. Look for exact matches to "{query}"
        2. Find similar/related products
        3. Check all product names, descriptions, categories, features
        4. Include specifications, prices, page numbers
        
        RESPONSE FORMAT:
        If matches found:
        - List all matching products with complete details
        - Include exact names, models, specifications, prices
        - Show page numbers and key features
        - Explain relevance to query
        
        If no matches:
        - State clearly no matches found
        - Suggest similar products if available
        - List main categories in catalog
        
        Be accurate and comprehensive using the pre-processed data.
        """
        
        try:
            response = self.gemini_service.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Search error in {self.catalog_name}: {e}")
            return f"Error searching {self.catalog_name}: {e}"

class OptimizedRelevanceScorer:
    """Optimized relevance scoring using pre-processed summaries"""
    
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
    
    async def score_catalogs_batch(self, query: str, catalog_agents: Dict[str, UnifiedCatalogAgent]) -> List[Tuple[str, float, str]]:
        """Score all catalogs efficiently using pre-processed summaries"""
        
        # Format all summaries at once
        formatted_summaries = self._format_all_summaries(catalog_agents)
        
        prompt = f"""
        USER QUERY: "{query}"
        
        CATALOG SUMMARIES:
        {formatted_summaries}
        
        TASK: Score each catalog 0-10 for relevance to query.
        
        SCORING CRITERIA:
        10: Perfect match - exact product in catalog
        8-9: Very high - similar products, same category
        6-7: Good - related category or features
        4-5: Moderate - some relevance
        1-3: Low - minimal connection
        0: No relevance - unrelated
        
        Return JSON array:
        [
            {{"catalog": "filename.pdf", "score": 9.0, "reason": "Contains multiple fan models"}},
            {{"catalog": "file2.pdf", "score": 2.0, "reason": "Only kitchen appliances"}}
        ]
        
        Include ALL catalogs with precise scores.
        """
        
        try:
            response = self.gemini_service.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean JSON response
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            scores = json.loads(response_text)
            
            # Convert to result format
            results = []
            for item in scores:
                catalog_name = item.get('catalog', '')
                score = float(item.get('score', 0))
                reason = item.get('reason', 'No reason provided')
                results.append((catalog_name, score, reason))
            
            results.sort(key=lambda x: x[1], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Error in batch scoring: {e}")
            return [(name, 5.0, "Fallback scoring") for name in catalog_agents.keys()]
    
    def _format_all_summaries(self, catalog_agents: Dict[str, UnifiedCatalogAgent]) -> str:
        """Format all summaries efficiently"""
        formatted = []
        
        for catalog_name, agent in catalog_agents.items():
            if not agent.is_initialized:
                continue
                
            summary = agent.get_summary_data()
            entry = f"""
CATALOG: {catalog_name}
Summary: {summary.get('detailed_summary', 'No summary')}
Products: {', '.join(summary.get('all_products', [])[:10])}
Categories: {', '.join(summary.get('product_categories', []))}
Brands: {', '.join(summary.get('brands', []))}
Keywords: {', '.join(summary.get('searchable_keywords', [])[:15])}
            """.strip()
            formatted.append(entry)
        
        return "\n\n".join(formatted)

class OptimizedAgentService:
    """Optimized service that eliminates redundant processing"""
    
    def __init__(self, catalog_service: CatalogService, gemini_service: GeminiService):
        self.catalog_service = catalog_service
        self.gemini_service = gemini_service
        self.unified_agents: Dict[str, UnifiedCatalogAgent] = {}
        self.relevance_scorer = OptimizedRelevanceScorer(gemini_service)
    
    async def initialize_catalog(self, catalog_name: str, pdf_path: str) -> None:
        """Initialize catalog with single comprehensive processing"""
        logger.info(f"OptimizedAgentService: Starting single-pass initialization for {catalog_name}")
        
        # Create unified agent
        agent = UnifiedCatalogAgent(catalog_name, self.gemini_service)
        
        # Single comprehensive initialization
        await agent.initialize_complete_catalog(pdf_path)
        
        # Store agent
        self.unified_agents[catalog_name] = agent
        
        logger.info(f"OptimizedAgentService: Single-pass initialization complete for {catalog_name}")
    
    async def process_query(self, query: str) -> str:
        """Process query using optimized system"""
        try:
            logger.info(f"Processing query with optimized system: {query}")
            
            if not self.unified_agents:
                return "No catalogs available for search."
            
            # Check if agents are ready
            ready_agents = {name: agent for name, agent in self.unified_agents.items() if agent.is_initialized}
            if not ready_agents:
                return "Catalogs are still being processed. Please wait a moment and try again."
            
            # Score all catalogs efficiently in one call
            scores = await self.relevance_scorer.score_catalogs_batch(query, ready_agents)
            
            if not scores:
                return "Error scoring catalogs for relevance."
            
            logger.info(f"Top catalog scores: {scores[:3]}")
            
            # Get best catalog
            best_catalog, best_score, reason = scores[0]
            
            if best_score < 1.0:
                categories = self._get_available_categories()
                return f"No relevant catalogs found for '{query}'. Available categories: {categories}"
            
            # Get agent (already initialized)
            best_agent = ready_agents.get(best_catalog)
            if not best_agent:
                return f"Error: Best catalog {best_catalog} not found in ready agents."
            
            # Search using pre-processed content
            detailed_response = await best_agent.search_products(query)
            
            # Try backup if response is poor
            if self._is_poor_response(detailed_response) and len(scores) > 1:
                for backup_catalog, backup_score, backup_reason in scores[1:3]:
                    if backup_score >= 3.0 and backup_catalog in ready_agents:
                        backup_agent = ready_agents[backup_catalog]
                        backup_response = await backup_agent.search_products(query)
                        
                        if not self._is_poor_response(backup_response):
                            best_catalog = backup_catalog
                            best_score = backup_score
                            detailed_response = backup_response
                            reason = backup_reason
                            break
            
            # Format response
            response = f"**🎯 Selected Catalog: {best_catalog}**\n"
            response += f"**📊 Relevance Score: {best_score:.1f}/10**\n"
            response += f"**💡 Selection Reason:** {reason}\n\n"
            response += f"**📋 Search Results:**\n{detailed_response}"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in optimized processing: {e}")
            return f"Error processing query: {e}"
    
    def _is_poor_response(self, response: str) -> bool:
        """Check if response indicates poor results"""
        poor_indicators = [
            "no exact matches", "no products matching", "not found",
            "sorry", "unable to find", "no information", "no relevant"
        ]
        return any(indicator in response.lower() for indicator in poor_indicators)
    
    def _get_available_categories(self) -> str:
        """Get available categories from all catalogs"""
        categories = set()
        for agent in self.unified_agents.values():
            if agent.is_initialized:
                summary = agent.get_summary_data()
                categories.update(summary.get('product_categories', []))
        return ', '.join(list(categories)[:5])
    
    def get_agent_count(self) -> int:
        """Get number of active agents"""
        return len([agent for agent in self.unified_agents.values() if agent.is_initialized])
    
    def get_summary_count(self) -> int:
        """Get number of initialized catalogs"""
        return len([agent for agent in self.unified_agents.values() if agent.is_initialized])