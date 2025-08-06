from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class PDFMetadata:
    """PDF catalog metadata model"""
    filename: str
    file_path: str
    summary: str = ""
    categories: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    product_types: List[str] = field(default_factory=list)
    brand_names: List[str] = field(default_factory=list)
    product_names: List[str] = field(default_factory=list)
    page_count: int = 0
    processing_date: Optional[datetime] = None
    is_processed: bool = False
    detailed_content: str = ""

@dataclass
class CatalogSearchResult:
    """Search result for catalog relevance"""
    catalog_name: str
    relevance_score: float
    reason: str = ""

@dataclass
class ChatMessage:
    """Chat message model"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)