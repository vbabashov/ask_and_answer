"""PDF metadata model for catalog information."""

from typing import List, Optional
from datetime import datetime


class PDFMetadata:
    """Stores metadata about a PDF catalog."""
    
    def __init__(self, filename: str, file_path: str):
        self.filename = filename
        self.file_path = file_path
        self.summary = ""
        self.categories: List[str] = []
        self.keywords: List[str] = []
        self.product_types: List[str] = []
        self.page_count = 0
        self.processing_date: Optional[datetime] = None
        self.is_processed = False
        self.detailed_content = ""  # Store more detailed content for better search
        
        # Additional metadata for better search
        self.brand_names: List[str] = []
        self.product_names: List[str] = []
        self.main_business_type = ""
    
    def to_dict(self) -> dict:
        """Convert metadata to dictionary for serialization."""
        return {
            'filename': self.filename,
            'file_path': self.file_path,
            'summary': self.summary,
            'categories': self.categories,
            'keywords': self.keywords,
            'product_types': self.product_types,
            'page_count': self.page_count,
            'processing_date': self.processing_date,
            'is_processed': self.is_processed,
            'detailed_content': self.detailed_content,
            'brand_names': self.brand_names,
            'product_names': self.product_names,
            'main_business_type': self.main_business_type
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PDFMetadata':
        """Create metadata object from dictionary."""
        instance = cls(data['filename'], data['file_path'])
        instance.summary = data.get('summary', '')
        instance.categories = data.get('categories', [])
        instance.keywords = data.get('keywords', [])
        instance.product_types = data.get('product_types', [])
        instance.page_count = data.get('page_count', 0)
        instance.processing_date = data.get('processing_date')
        instance.is_processed = data.get('is_processed', False)
        instance.detailed_content = data.get('detailed_content', '')
        instance.brand_names = data.get('brand_names', [])
        instance.product_names = data.get('product_names', [])
        instance.main_business_type = data.get('main_business_type', '')
        return instance
    
    def __repr__(self) -> str:
        return f"PDFMetadata(filename='{self.filename}', pages={self.page_count}, processed={self.is_processed})"