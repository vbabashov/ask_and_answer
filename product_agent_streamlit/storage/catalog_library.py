"""Catalog library storage and management."""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple

from models.pdf_metadata import PDFMetadata
from processors.pdf_processor import PDFCatalogProcessor
from config import DEFAULT_STORAGE_DIR, METADATA_FILENAME, DEFAULT_TOP_K


class CatalogLibrary:
    """Manages multiple PDF catalogs and their metadata."""
    
    def __init__(self, storage_dir: str = DEFAULT_STORAGE_DIR):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.catalogs: Dict[str, PDFMetadata] = {}
        
    def add_catalog(self, pdf_file, processor: PDFCatalogProcessor) -> PDFMetadata:
        """Add a new catalog to the library."""
        # Create unique filename
        filename = pdf_file.name
        file_path = self.storage_dir / filename
        
        # Save uploaded file
        with open(file_path, 'wb') as f:
            f.write(pdf_file.getvalue())
        
        # Process PDF for metadata
        images = processor.pdf_to_images(str(file_path))
        metadata = processor.generate_pdf_metadata(images, filename)
        metadata.file_path = str(file_path)
        
        # Store metadata
        self.catalogs[filename] = metadata
        self._save_metadata()
        
        return metadata
    
    def _save_metadata(self):
        """Save catalog metadata to disk."""
        metadata_file = self.storage_dir / METADATA_FILENAME
        with open(metadata_file, 'wb') as f:
            pickle.dump(self.catalogs, f)
    
    def _load_metadata(self):
        """Load catalog metadata from disk."""
        metadata_file = self.storage_dir / METADATA_FILENAME
        if metadata_file.exists():
            try:
                with open(metadata_file, 'rb') as f:
                    self.catalogs = pickle.load(f)
            except Exception as e:
                print(f"Error loading metadata: {e}")
                self.catalogs = {}
    
    def get_catalog_summaries(self) -> str:
        """Get formatted summaries of all catalogs."""
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
            Brand Names: {', '.join(getattr(metadata, 'brand_names', []))}
            Product Names: {', '.join(getattr(metadata, 'product_names', []))}
            Pages: {metadata.page_count}
            """
            summaries.append(summary.strip())
        
        return "\n\n".join(summaries)
    
    def search_relevant_catalogs(self, query: str, processor: PDFCatalogProcessor, top_k: int = DEFAULT_TOP_K) -> List[Tuple[str, float]]:
        """Search for the most relevant catalogs based on query with improved scoring."""
        if not self.catalogs:
            return []
        
        try:
            print(f"\n=== CATALOG SEARCH DEBUG ===")
            print(f"Query: {query}")
            print(f"Available catalogs: {list(self.catalogs.keys())}")
            
            # Enhanced search prompt with better instructions
            search_prompt = f"""
            You are a catalog relevance expert. Given this user query: "{query}"
            
            And these available catalogs:
            {self.get_catalog_summaries()}
            
            TASK: Rank ALL catalogs by relevance to the query (0-10 scale, 10 being most relevant).
            
            SCORING GUIDELINES:
            - 10: Perfect match (exact product mentioned in catalog)
            - 8-9: Very high match (similar products, same category)
            - 6-7: Good match (related products or category)
            - 4-5: Moderate match (some relevance)
            - 1-3: Low match (minimal relevance)
            - 0: No match (completely unrelated)
            
            IMPORTANT: Consider these factors in order of importance:
            1. Exact product name matches
            2. Product type/category matches  
            3. Brand name matches
            4. Keyword matches
            5. General relevance
            
            Return ONLY a JSON array with this exact format:
            [
                {{"catalog": "exact_filename.pdf", "relevance_score": 9, "reason": "Contains Temperature Glass Kettle products"}},
                {{"catalog": "exact_filename2.pdf", "relevance_score": 2, "reason": "Only contains espresso machines, not kettles"}}
            ]
            
            Include ALL catalogs in the response with their scores.
            Return only the JSON, no other text.
            """
            
            response = processor.model.generate_content(search_prompt)
            print(f"Raw search response: {response.text}")
            
            return self._parse_search_response(response.text, top_k)
        
        except Exception as e:
            print(f"Error in catalog search: {e}")
            return [(filename, 5.0) for filename in list(self.catalogs.keys())[:top_k]]

    def _parse_search_response(self, response_text: str, top_k: int) -> List[Tuple[str, float]]:
        """Parse the search response and return ranked results."""
        try:
            # Clean the response text
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            rankings = json.loads(response_text.strip())
            results = []
            
            print(f"Parsed rankings: {rankings}")
            
            for item in rankings:
                catalog_name = item.get('catalog')
                score = item.get('relevance_score', 0)
                reason = item.get('reason', 'No reason provided')
                
                if catalog_name in self.catalogs:
                    results.append((catalog_name, float(score)))
                    print(f"  {catalog_name}: {score}/10 - {reason}")
                else:
                    print(f"  WARNING: Catalog '{catalog_name}' not found in library")
            
            # Sort by relevance score and return top_k
            results.sort(key=lambda x: x[1], reverse=True)
            print(f"Final ranked results: {results[:top_k]}")
            return results[:top_k]
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response_text}")
            # Fallback: return all catalogs with equal scores
            fallback_results = [(filename, 5.0) for filename in list(self.catalogs.keys())[:top_k]]
            print(f"Using fallback results: {fallback_results}")
            return fallback_results

    def get_catalog_by_name(self, catalog_name: str) -> PDFMetadata:
        """Get catalog metadata by name."""
        return self.catalogs.get(catalog_name)

    def remove_catalog(self, catalog_name: str) -> bool:
        """Remove a catalog from the library."""
        if catalog_name in self.catalogs:
            # Remove file
            file_path = Path(self.catalogs[catalog_name].file_path)
            if file_path.exists():
                file_path.unlink()
            
            # Remove from catalog dict
            del self.catalogs[catalog_name]
            self._save_metadata()
            return True
        return False

    def get_catalog_count(self) -> int:
        """Get total number of catalogs."""
        return len(self.catalogs)