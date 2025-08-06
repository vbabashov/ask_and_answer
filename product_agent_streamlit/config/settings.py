# File: config/settings.py
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Application configuration"""
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    storage_dir: str = "catalog_storage"
    agent_llm_name: str = "gemini-2.5-flash"
    max_batch_size: int = 10
    max_catalogs: int = 300
    dpi: int = 200
    
    def __post_init__(self):
        # Load from environment if not provided
        if not self.gemini_api_key:
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    def validate(self) -> bool:
        """Validate required configuration"""
        return bool(self.gemini_api_key and self.openai_api_key)