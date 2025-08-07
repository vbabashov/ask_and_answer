"""
PDF Metadata model for storing catalog information
"""

from typing import List, Optional
from datetime import datetime

class PDFMetadata:
    """Stores metadata about a PDF catalog."""
    
    def __init__(self, filename: str, file_path: str):
        self.filename = filename
        self.file_path = file_path
        self.summary = ""
        self.categories = []
        self.keywords = []
        self.product_types = []
        self.page_count = 0
        self.processing_date = None
        self.is_processed = False
        self.detailed_content = ""  # Store more detailed content for better search
        self.brand_names = []  # Additional metadata for better search
        self.product_names = []  # Additional metadata for better search