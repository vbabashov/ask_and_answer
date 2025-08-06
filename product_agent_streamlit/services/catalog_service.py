from typing import Dict, List, Optional
import logging
from datetime import datetime

# Import from other packages
from models import PDFMetadata, CatalogSearchResult
from repositories import CatalogRepository
from services.gemini_service import GeminiService
from utils import pdf_to_images

logger = logging.getLogger(__name__)

class CatalogService:
    """Service for catalog management operations"""
    
    def __init__(self, repository: CatalogRepository, gemini_service: GeminiService):
        self.repository = repository
        self.gemini_service = gemini_service
        self.catalogs: Dict[str, PDFMetadata] = repository.load_metadata()
    
    def add_catalog(self, pdf_file, dpi: int = 200) -> PDFMetadata:
        """Add a new catalog to the library"""
        filename = pdf_file.name
        logger.info(f"Adding catalog: {filename}")
        
        # Save PDF file
        file_path = self.repository.save_pdf(pdf_file, filename)
        
        # Process PDF
        images = pdf_to_images(file_path, dpi)
        metadata_dict = self.gemini_service.generate_metadata(images, filename)
        
        # Create metadata object
        metadata = PDFMetadata(
            filename=filename,
            file_path=file_path,
            summary=metadata_dict.get("summary", f"Product catalog: {filename}"),
            categories=metadata_dict.get("categories", ["general"]),
            keywords=metadata_dict.get("keywords", []),
            product_types=metadata_dict.get("product_types", []),
            brand_names=metadata_dict.get("brand_names", []),
            product_names=metadata_dict.get("product_names", []),
            page_count=len(images),
            processing_date=datetime.now(),
            is_processed=True
        )
        
        # Store metadata
        self.catalogs[filename] = metadata
        self.repository.save_metadata(self.catalogs)
        
        logger.info(f"Successfully added catalog: {filename}")
        return metadata
    
    def get_catalog_summaries(self) -> str:
        """Get formatted summaries of all catalogs"""
        if not self.catalogs:
            return "No catalogs available."
        
        summaries = []
        for filename, metadata in self.catalogs.items():
            summary = f"""
            Catalog: {filename}
            Summary: {metadata.summary}
            Categories: {', '.join(metadata.categories)}
            Product Types: {', '.join(metadata.product_types)}
            Keywords: {', '.join(metadata.keywords)}
            Brand Names: {', '.join(metadata.brand_names)}
            Product Names: {', '.join(metadata.product_names)}
            Pages: {metadata.page_count}
            """
            summaries.append(summary.strip())
        
        return "\n\n".join(summaries)
    
    def search_relevant_catalogs(self, query: str, top_k: int = 3) -> List[CatalogSearchResult]:
        """Search for the most relevant catalogs based on query"""
        if not self.catalogs:
            return []
        
        try:
            logger.info(f"Searching catalogs for query: {query}")
            
            # First do local keyword matching as a baseline
            local_scores = self._calculate_local_scores(query)
            
            # Get catalog summaries for Gemini
            catalog_summaries = self.get_catalog_summaries()
            
            # Get Gemini scores
            gemini_rankings = self.gemini_service.search_catalogs(query, catalog_summaries)
            
            # Combine scores
            results = self._combine_scores(local_scores, gemini_rankings)
            
            # Sort by relevance score and return top_k
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            logger.info(f"Final catalog ranking: {[(r.catalog_name, r.relevance_score) for r in results[:top_k]]}")
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in catalog search: {e}")
            # Fallback: return all catalogs with equal scores
            return [
                CatalogSearchResult(filename, 5.0, "Fallback result")
                for filename in list(self.catalogs.keys())[:top_k]
            ]

    def _calculate_local_scores(self, query: str) -> Dict[str, float]:
        """Calculate local keyword-based scores"""
        query_terms = query.lower().split()
        scores = {}
        
        for filename, metadata in self.catalogs.items():
            score = 0.0
            
            # Check keywords (highest weight)
            for keyword in metadata.keywords:
                for term in query_terms:
                    if term in keyword.lower():
                        score += 3.0
            
            # Check product names (high weight)
            for product_name in metadata.product_names:
                for term in query_terms:
                    if term in product_name.lower():
                        score += 2.5
            
            # Check categories (medium weight)
            for category in metadata.categories:
                for term in query_terms:
                    if term in category.lower():
                        score += 2.0
            
            # Check summary (low weight)
            summary_lower = metadata.summary.lower()
            for term in query_terms:
                if term in summary_lower:
                    score += 1.0
            
            scores[filename] = min(score, 10.0)  # Cap at 10
            logger.info(f"Local score for {filename}: {score}")
        
        return scores

    def _combine_scores(self, local_scores: Dict[str, float], gemini_rankings: List[Dict]) -> List[CatalogSearchResult]:
        """Combine local and Gemini scores"""
        results = []
        
        # Create a map of Gemini scores
        gemini_scores = {item.get('catalog', ''): item.get('relevance_score', 0) for item in gemini_rankings}
        
        for filename in self.catalogs.keys():
            local_score = local_scores.get(filename, 0.0)
            gemini_score = gemini_scores.get(filename, 0.0)
            
            # Weighted combination (60% local, 40% Gemini)
            combined_score = (0.6 * local_score) + (0.4 * gemini_score)
            
            reason = f"Local: {local_score:.1f}, Gemini: {gemini_score:.1f}"
            
            results.append(CatalogSearchResult(
                catalog_name=filename,
                relevance_score=combined_score,
                reason=reason
            ))
        
        return results
    
    def _preprocess_query(self, query: str) -> List[str]:
        """Extract key terms from user query"""
        import re
        
        # Remove common words
        stop_words = {'what', 'is', 'the', 'how', 'do', 'does', 'can', 'will', 'would', 'should', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'about'}
        
        # Extract meaningful terms
        terms = re.findall(r'\b\w+\b', query.lower())
        key_terms = [term for term in terms if term not in stop_words and len(term) > 2]
        
        logger.info(f"Extracted key terms from '{query}': {key_terms}")
        return key_terms
    def get_catalog_by_name(self, catalog_name: str) -> Optional[PDFMetadata]:
        """Get catalog metadata by name"""
        return self.catalogs.get(catalog_name)
    
    def get_all_catalogs(self) -> Dict[str, PDFMetadata]:
        """Get all catalog metadata"""
        return self.catalogs.copy()