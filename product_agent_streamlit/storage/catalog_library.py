"""
Fixed catalog library for managing multiple PDF catalogs and their metadata
Key improvements:
1. Better keyword-based scoring with fallbacks
2. More robust search logic
3. Improved metadata extraction
4. Better catalog differentiation
"""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple
import re
from difflib import SequenceMatcher

from models.pdf_metadata import PDFMetadata
from processors.pdf_processor import PDFCatalogProcessor

class CatalogLibrary:
    """Manages multiple PDF catalogs and their metadata."""
    
    def __init__(self, storage_dir: str = "catalog_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.catalogs: Dict[str, PDFMetadata] = {}
        self.processor = None
        
    def add_catalog(self, pdf_file, processor: PDFCatalogProcessor) -> PDFMetadata:
        """Add a new catalog to the library."""
        # Create unique filename
        filename = pdf_file.name
        file_path = self.storage_dir / filename
        
        # Save uploaded file
        with open(file_path, 'wb') as f:
            f.write(pdf_file.getvalue())
        
        # Process PDF for metadata with enhanced extraction
        images = processor.pdf_to_images(str(file_path))
        metadata = processor.generate_pdf_metadata(images, filename)
        metadata.file_path = str(file_path)
        
        # Store metadata
        self.catalogs[filename] = metadata
        self._save_metadata()
        
        print(f"Added catalog {filename} with metadata:")
        print(f"  Categories: {metadata.categories}")
        print(f"  Product Types: {metadata.product_types}")
        print(f"  Keywords: {metadata.keywords}")
        print(f"  Brand Names: {getattr(metadata, 'brand_names', [])}")
        print(f"  Product Names: {getattr(metadata, 'product_names', [])}")
        
        return metadata
    
    def _save_metadata(self):
        """Save catalog metadata to disk."""
        metadata_file = self.storage_dir / "catalog_metadata.pkl"
        with open(metadata_file, 'wb') as f:
            pickle.dump(self.catalogs, f)
    
    def _load_metadata(self):
        """Load catalog metadata from disk."""
        metadata_file = self.storage_dir / "catalog_metadata.pkl"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'rb') as f:
                    self.catalogs = pickle.load(f)
                print(f"Loaded {len(self.catalogs)} catalogs from metadata file")
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
    
    def _calculate_keyword_similarity(self, query: str, metadata: PDFMetadata) -> float:
        """Calculate similarity score based on keyword matching."""
        query_lower = query.lower()
        query_words = re.findall(r'\w+', query_lower)
        
        total_score = 0.0
        max_possible_score = 0.0
        
        # Weight different metadata fields
        field_weights = {
            'product_names': 10.0,  # Highest weight for exact product names
            'brand_names': 8.0,
            'product_types': 7.0,
            'categories': 5.0,
            'keywords': 3.0
        }
        
        for field_name, weight in field_weights.items():
            field_data = getattr(metadata, field_name, [])
            if not field_data:
                continue
                
            field_score = 0.0
            field_items = [str(item).lower() for item in field_data]
            
            for query_word in query_words:
                best_match_score = 0.0
                
                for item in field_items:
                    # Exact word match
                    if query_word in item:
                        best_match_score = max(best_match_score, 1.0)
                    # Fuzzy match for similar words
                    else:
                        for item_word in re.findall(r'\w+', item):
                            if len(query_word) > 3 and len(item_word) > 3:
                                similarity = SequenceMatcher(None, query_word, item_word).ratio()
                                if similarity > 0.8:
                                    best_match_score = max(best_match_score, similarity)
                
                field_score += best_match_score
            
            # Normalize field score by number of query words
            if query_words:
                field_score = (field_score / len(query_words)) * weight
            
            total_score += field_score
            max_possible_score += weight
        
        # Also check summary for additional context
        summary_score = 0.0
        if metadata.summary:
            summary_lower = metadata.summary.lower()
            for query_word in query_words:
                if query_word in summary_lower:
                    summary_score += 1.0
            if query_words:
                summary_score = (summary_score / len(query_words)) * 2.0  # Lower weight for summary
        
        total_score += summary_score
        max_possible_score += 2.0
        
        # Normalize to 0-10 scale
        if max_possible_score > 0:
            normalized_score = (total_score / max_possible_score) * 10.0
            return min(10.0, normalized_score)
        
        return 0.0
    
    def search_relevant_catalogs(self, query: str, processor: PDFCatalogProcessor, top_k: int = 3) -> List[Tuple[str, float]]:
        """Search for the most relevant catalogs with improved hybrid approach."""
        if not self.catalogs:
            print("No catalogs available for search")
            return []
        
        print(f"\n=== ENHANCED CATALOG SEARCH ===")
        print(f"Query: {query}")
        print(f"Available catalogs: {list(self.catalogs.keys())}")
        
        # First, use keyword-based scoring as primary method
        keyword_results = []
        for filename, metadata in self.catalogs.items():
            score = self._calculate_keyword_similarity(query, metadata)
            keyword_results.append((filename, score, "keyword_match"))
            print(f"Keyword score for {filename}: {score:.2f}")
        
        # Sort by keyword scores
        keyword_results.sort(key=lambda x: x[1], reverse=True)
        
        # If we have good keyword matches (score > 3), use them
        good_matches = [(name, score) for name, score, method in keyword_results if score > 3.0]
        if good_matches:
            print(f"Using keyword-based results: {good_matches[:top_k]}")
            return good_matches[:top_k]
        
        # Fallback to LLM-based scoring for complex queries
        print("Keyword matching insufficient, trying LLM-based scoring...")
        try:
            llm_results = self._llm_based_search(query, processor)
            if llm_results:
                print(f"Using LLM-based results: {llm_results[:top_k]}")
                return llm_results[:top_k]
        except Exception as e:
            print(f"LLM search failed: {e}")
        
        # Final fallback: return all catalogs with equal scores
        fallback_results = [(name, 5.0) for name, _, _ in keyword_results[:top_k]]
        print(f"Using fallback results: {fallback_results}")
        return fallback_results
    
    def _llm_based_search(self, query: str, processor: PDFCatalogProcessor) -> List[Tuple[str, float]]:
        """LLM-based search as fallback method."""
        try:
            # Create a more structured prompt for better results
            catalog_info = []
            for filename, metadata in self.catalogs.items():
                info = {
                    "filename": filename,
                    "summary": metadata.summary,
                    "categories": metadata.categories,
                    "product_types": metadata.product_types,
                    "keywords": metadata.keywords,
                    "brand_names": getattr(metadata, 'brand_names', []),
                    "product_names": getattr(metadata, 'product_names', [])
                }
                catalog_info.append(info)
            
            search_prompt = f"""
            User query: "{query}"
            
            Available catalogs:
            {json.dumps(catalog_info, indent=2)}
            
            Rate each catalog's relevance to the query on a scale of 0-10:
            - 10: Perfect match (exact product/category mentioned)
            - 8-9: Very relevant (similar products/category)
            - 6-7: Somewhat relevant (related domain)
            - 4-5: Marginally relevant
            - 0-3: Not relevant
            
            Return ONLY a JSON array:
            [
                {{"catalog": "filename1.pdf", "score": 9, "reason": "Contains exact product"}},
                {{"catalog": "filename2.pdf", "score": 2, "reason": "Different category"}}
            ]
            """
            
            response = processor.model.generate_content(search_prompt)
            response_text = response.text.strip()
            
            # Clean JSON response
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            rankings = json.loads(response_text)
            results = []
            
            for item in rankings:
                catalog_name = item.get('catalog')
                score = float(item.get('score', 0))
                
                if catalog_name in self.catalogs:
                    results.append((catalog_name, score))
                    print(f"LLM score for {catalog_name}: {score}")
            
            results.sort(key=lambda x: x[1], reverse=True)
            return results
            
        except Exception as e:
            print(f"LLM search error: {e}")
            return []