import os
# os.environ['PATH']+= r';C:\Users\vusal.babashov\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-\24.08.0\Library\bin'
# os.environ['PATH']+= r';C:\Users\vusal.babashov\AppData\Local\ProgramsTesseract-OCR'

# # # Configure Tesseract path
# import pytesseract
# pytesseract.pytesseract.tesseract_cmd = r'C:\Users\vusal.babashov\AppData\Local\ProgramsTesseract-OCR\tesseract.exe'

from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import asyncio

from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.embeddings.azure_openai import AzureOpenAIEmbeddings
from dotenv import load_dotenv
from utils.azure_openai.client import get_openai_client
# from utils.mongodb.vector_store import MongoVectorStore


@dataclass
class ManualMetadata:
    brand: str
    product_num: str
    language: str
    file_path: str

class PDFProcessor:
    def __init__(
        self,
        base_folder: str,
    ):
        """
        Initialize the PDF processor
        
        Args:
            base_folder: Path to the Manuals folder on Desktop
            azure_endpoint: Azure OpenAI endpoint URL
            api_key: Azure OpenAI API key
            deployment_name: Name of the embedding model deployment
            mongodb_uri: MongoDB connection string, if None will be read from env
        """
        self.base_folder = Path(base_folder)
        self.client = get_openai_client()
        # self.vector_store = MongoVectorStore(connection_string=mongodb_uri)

    async def create_embeddings(self, text: str) -> List[float]:
        """Create embeddings using Azure OpenAI"""
        response = await self.client.embeddings.create(
            model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            input=text
        )
        return response.data[0].embedding

    def discover_manuals(self) -> List[ManualMetadata]:
        """Walk through the directory structure and discover all PDF manuals."""
        manuals = []
        
        for brand_folder in self.base_folder.iterdir():
            if not brand_folder.is_dir():
                continue
                
            for product_folder in brand_folder.iterdir():
                if not product_folder.is_dir():
                    continue
                    
                for manual_file in product_folder.glob("*.pdf"):
                    # Determine language based on filename
                    filename_lower = manual_file.name.lower()
                    if "EN-FR" in filename_lower or "FR-EN" in filename_lower:
                        language = "EN-FR"
                    elif "_FR" in filename_lower:
                        language = "FR"
                    else:
                        language = "EN"

                    manual = ManualMetadata(
                        brand=brand_folder.name,
                        product_num=product_folder.name,
                        language=language,
                        file_path=str(manual_file)
                    )
                    manuals.append(manual)
        
        return manuals
    
    async def process_pdf(self, manual: ManualMetadata) -> List[Dict[str, Any]]:
        """
        Process a single PDF file:
        1. Load and parse with OCR
        2. Split into pages
        3. Generate embeddings
        
        Returns a list of dictionaries containing page content, embeddings, and metadata
        """
        # Load PDF with OCR enabled
        loader = UnstructuredPDFLoader(
            manual.file_path,
            # strategy="ocr_only",
            # post_process=True
            # strategy="fast",
            mode="elements",
            languages=['eng', 'fra'],
            # pdf_image_dpi=200,
            # extract_images_in_pdf=True,
            # skip_page_after_n_chars=100000  # Adjust if needed
        )
        
        # Load the document
        document = loader.load()
        # print("after document load:", document)
        
        # Split by pages (using a large chunk size to keep pages together)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        pages = text_splitter.split_documents(document)
    

        # Process each page
        results = []
        for i, page in enumerate(pages):
            # Generate embedding for the page
            embedding = await self.create_embeddings(page.page_content)
            # print(embedding)
            
            # Create result dictionary
            result = {
                "content": page.page_content,
                "embedding": embedding,
                "metadata": {
                    "brand": manual.brand,
                    "product_num": manual.product_num,
                    "language": manual.language,
                    "page_number": i + 1,
                    "file_path": manual.file_path
                }
            }
            results.append(result)
            
        return results

def main():
    # Load environment variables
    load_dotenv()

    # Get the Manuals folder path
    manuals_folder = os.path.join(os.path.expanduser("~"), "OneDrive - Canadian Tire", "Desktop", "Manuals", "tests")

    # Initialize processor
    processor = PDFProcessor(
        base_folder=manuals_folder
    )

    async def process_manuals():
        # Discover all manuals
        manuals = processor.discover_manuals()
        print(f"Found {len(manuals)} manuals to process")

        # Process each manual
        for manual in manuals:
            print(f"Processing {manual.file_path}...")
            try:
                results = await processor.process_pdf(manual)
                print(f"Generated {len(results)} page embeddings")
            except Exception as e:
                print(f"Error processing {manual.file_path}: {str(e)}")

    asyncio.run(process_manuals())

if __name__ == "__main__":
    main()
