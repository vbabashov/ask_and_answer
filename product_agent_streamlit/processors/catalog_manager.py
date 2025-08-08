# catalog_manager.py
from typing import Dict
from dataclasses import dataclass

@dataclass
class CatalogInfo:
    filename: str
    content: str
    summary: str
    page_count: int

class CatalogManager:
    def __init__(self):
        self.catalogs: Dict[str, CatalogInfo] = {}
    
    def add_catalog(self, filename: str, content: str, summary: str, page_count: int):
        """Add catalog to the manager."""
        self.catalogs[filename] = CatalogInfo(filename, content, summary, page_count)
    
    def get_catalog_content(self, filename: str) -> str:
        """Get full catalog content."""
        if filename in self.catalogs:
            return self.catalogs[filename].content
        return ""
    
    def get_catalog_summary(self, filename: str) -> str:
        """Get catalog summary."""
        if filename in self.catalogs:
            return self.catalogs[filename].summary
        return ""
    
    def get_all_summaries(self) -> str:
        """Get formatted summaries of all catalogs."""
        if not self.catalogs:
            return "No catalogs available."
        
        result = f"**📚 Available Catalogs ({len(self.catalogs)}):**\n\n"
        
        for i, (filename, info) in enumerate(self.catalogs.items(), 1):
            result += f"**{i}. {filename}**\n"
            result += f"   📄 Pages: {info.page_count}\n"
            result += f"   📋 Summary: {info.summary}\n\n"
        
        return result