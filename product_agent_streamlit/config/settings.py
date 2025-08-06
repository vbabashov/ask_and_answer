# # File: config/settings.py
# import os
# from dataclasses import dataclass
# from typing import Optional
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# @dataclass
# class Config:
#     """Application configuration"""
#     gemini_api_key: Optional[str] = None
#     openai_api_key: Optional[str] = None
#     storage_dir: str = "catalog_storage"
#     agent_llm_name: str = "gemini-2.5-flash"
#     max_batch_size: int = 10
#     max_catalogs: int = 300
#     dpi: int = 200
    
#     def __post_init__(self):
#         # Load from environment if not provided
#         if not self.gemini_api_key:
#             self.gemini_api_key = os.getenv("GEMINI_API_KEY")
#         if not self.openai_api_key:
#             self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
#     def validate(self) -> bool:
#         """Validate required configuration"""
#         return bool(self.gemini_api_key and self.openai_api_key)


# config/settings.py - Updated for Gemini-Only Agent System
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Application configuration for Gemini-Only Agent System"""
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None  # Keep for compatibility but not required
    storage_dir: str = "catalog_storage"
    agent_llm_name: str = "gemini-2.5-flash"  # Changed back to Gemini
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
        """Validate required configuration for Gemini-Only Agent System"""
        # Only Gemini API key is required now
        has_gemini = bool(self.gemini_api_key)
        
        if not has_gemini:
            print("❌ Gemini API key is required for all operations")
            
        return has_gemini