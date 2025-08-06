# File: repositories/catalog_repository.py
import pickle
from pathlib import Path
from typing import Dict, Optional
import logging

# Import from models package
from models import PDFMetadata

logger = logging.getLogger(__name__)

class CatalogRepository:
    """Repository for catalog metadata persistence"""
    
    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.metadata_file = self.storage_dir / "catalog_metadata.pkl"
    
    def save_metadata(self, catalogs: Dict[str, PDFMetadata]) -> None:
        """Save catalog metadata to disk"""
        try:
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(catalogs, f)
            logger.info(f"Saved metadata for {len(catalogs)} catalogs")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def load_metadata(self) -> Dict[str, PDFMetadata]:
        """Load catalog metadata from disk"""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'rb') as f:
                catalogs = pickle.load(f)
            logger.info(f"Loaded metadata for {len(catalogs)} catalogs")
            return catalogs
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return {}
    
    def save_pdf(self, pdf_file, filename: str) -> str:
        """Save uploaded PDF file"""
        file_path = self.storage_dir / filename
        try:
            with open(file_path, 'wb') as f:
                f.write(pdf_file.getvalue())
            logger.info(f"Saved PDF: {filename}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving PDF {filename}: {e}")
            raise