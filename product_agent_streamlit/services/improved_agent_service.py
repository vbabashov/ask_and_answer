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