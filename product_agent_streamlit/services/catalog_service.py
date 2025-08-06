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
            
            # Get catalog summaries
            catalog_summaries = self.get_catalog_summaries()
            
            # Search using Gemini
            rankings = self.gemini_service.search_catalogs(query, catalog_summaries)
            
            results = []
            for item in rankings:
                catalog_name = item.get('catalog')
                score = item.get('relevance_score', 0)
                reason = item.get('reason', 'No reason provided')
                
                if catalog_name in self.catalogs:
                    results.append(CatalogSearchResult(
                        catalog_name=catalog_name,
                        relevance_score=float(score),
                        reason=reason
                    ))
            
            # Sort by relevance score and return top_k
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            print("THIS IS THE FINAL RELEVANT CATALOGS", results)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in catalog search: {e}")
            # Fallback: return all catalogs with equal scores
            return [
                CatalogSearchResult(filename, 5.0, "Fallback result")
                for filename in list(self.catalogs.keys())[:top_k]
            ]
    
    def get_catalog_by_name(self, catalog_name: str) -> Optional[PDFMetadata]:
        """Get catalog metadata by name"""
        return self.catalogs.get(catalog_name)
    
    def get_all_catalogs(self) -> Dict[str, PDFMetadata]:
        """Get all catalog metadata"""
        return self.catalogs.copy()