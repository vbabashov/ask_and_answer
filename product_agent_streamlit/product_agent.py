import asyncio
import contextlib
import logging
import os
import signal
import sys
import tempfile
import json
import pickle
from pathlib import Path
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image
import agents
import streamlit as st
from dotenv import load_dotenv
from openai import AsyncOpenAI
import google.generativeai as genai
import base64
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv(verbose=True)

logging.basicConfig(level=logging.INFO)

AGENT_LLM_NAME = "gemini-2.5-flash"

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

class PDFCatalogProcessor:
    """Handles PDF processing and analysis using Gemini."""
    
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def pdf_to_images(self, pdf_path: str, dpi: int = 200) -> List[Image.Image]:
        """Convert PDF pages to PIL Images for processing."""
        try:
            pdf_document = fitz.open(pdf_path)
            images = []
            
            print(f"Converting {pdf_document.page_count} pages to images...")
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                mat = fitz.Matrix(dpi/72, dpi/72)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(BytesIO(img_data))
                images.append(img)
                print(f"Processed page {page_num + 1}/{pdf_document.page_count}")
            
            pdf_document.close()
            return images
            
        except Exception as e:
            raise Exception(f"Error converting PDF: {str(e)}")
    
    def analyze_catalog_batch(self, images: List[Image.Image], batch_start: int) -> str:
        """Analyze a batch of catalog pages."""
        analysis_prompt = f"""
        You are analyzing pages {batch_start + 1} to {batch_start + len(images)} of a product catalog.
        
        Extract ALL information including:
        - Product names, models, SKUs, and exact product identifiers
        - Complete descriptions and features  
        - Prices and pricing variations
        - Technical specifications and dimensions
        - Categories, sections, and product types
        - Brand names and manufacturers
        - Contact information
        - Special offers or promotions
        - Page numbers for reference
        
        IMPORTANT: Be extremely thorough and extract ALL visible text including text in images.
        Pay special attention to product names and variations.
        
        Format the response as structured data that can be easily searched and referenced.
        Include a product list at the beginning with all product names found.
        """
        
        try:
            response = self.model.generate_content([analysis_prompt] + images)
            return response.text
        except Exception as e:
            return f"Error analyzing batch starting at page {batch_start + 1}: {str(e)}"

    def generate_pdf_metadata(self, images: List[Image.Image], filename: str) -> PDFMetadata:
        """Generate metadata and summary for a PDF catalog."""
        try:
            # Sample first few pages for metadata generation
            sample_images = images[:min(8, len(images))]  # Increased sample size
            
            metadata_prompt = """
            Analyze this product catalog thoroughly and provide metadata in the following JSON format:
            {
                "summary": "Detailed 3-4 sentence summary of what this catalog contains, including specific product types and brands",
                "categories": ["category1", "category2", "category3", "category4", "category5"],
                "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8"],
                "product_types": ["specific_product_type1", "specific_product_type2", "specific_product_type3"],
                "main_business_type": "detailed description of business type",
                "brand_names": ["brand1", "brand2", "brand3"],
                "product_names": ["specific_product_name1", "specific_product_name2", "specific_product_name3"]
            }
            
            Focus on:
            - Exact product names and model numbers
            - Specific product categories (e.g., "glass kettles", "espresso machines", "blenders")
            - Brand names and manufacturers
            - Product features and characteristics
            - Target market or industry
            - Key specializations
            
            Be very specific with product types and names. Avoid generic terms.
            Provide only the JSON response, no other text.
            """
            
            response = self.model.generate_content([metadata_prompt] + sample_images)
            
            # Parse JSON response
            try:
                metadata_json = json.loads(response.text.strip())
                print(f"Generated metadata for {filename}: {metadata_json}")
            except Exception as json_error:
                print(f"JSON parsing error: {json_error}")
                print(f"Raw response: {response.text}")
                # Fallback if JSON parsing fails
                metadata_json = {
                    "summary": f"Product catalog: {filename}",
                    "categories": ["general"],
                    "keywords": [filename.replace('.pdf', '').lower()],
                    "product_types": ["products"],
                    "main_business_type": "retail",
                    "brand_names": [],
                    "product_names": []
                }
            
            # Create metadata object
            metadata = PDFMetadata(filename, "")
            metadata.summary = metadata_json.get("summary", f"Product catalog: {filename}")
            metadata.categories = metadata_json.get("categories", ["general"])
            metadata.keywords = metadata_json.get("keywords", [])
            metadata.product_types = metadata_json.get("product_types", [])
            metadata.page_count = len(images)
            metadata.is_processed = True
            
            # Store additional metadata for better search
            metadata.brand_names = metadata_json.get("brand_names", [])
            metadata.product_names = metadata_json.get("product_names", [])
            
            return metadata
            
        except Exception as e:
            print(f"Error generating metadata for {filename}: {str(e)}")
            # Return basic metadata
            metadata = PDFMetadata(filename, "")
            metadata.summary = f"Product catalog: {filename}"
            metadata.categories = ["general"]
            metadata.keywords = [filename.replace('.pdf', '').lower()]
            metadata.product_types = ["products"]
            metadata.page_count = len(images)
            return metadata

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
    
    def search_relevant_catalogs(self, query: str, processor: PDFCatalogProcessor, top_k: int = 3) -> List[Tuple[str, float]]:
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
            
            try:
                # Clean the response text
                response_text = response.text.strip()
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
                print(f"Response text: {response.text}")
                # Fallback: return all catalogs with equal scores
                fallback_results = [(filename, 5.0) for filename in list(self.catalogs.keys())[:top_k]]
                print(f"Using fallback results: {fallback_results}")
                return fallback_results
        
        except Exception as e:
            print(f"Error in catalog search: {e}")
            return [(filename, 5.0) for filename in list(self.catalogs.keys())[:top_k]]

class OrchestratorTools:
    """Tools for the orchestrator agent."""
    
    def __init__(self, catalog_library: CatalogLibrary, processor: PDFCatalogProcessor, multi_system):
        self.catalog_library = catalog_library
        self.processor = processor
        self.multi_system = multi_system  # Reference to the MultiCatalogSystem
        
    async def answer_query_with_best_catalog(self, query: str) -> str:
        """Select the best catalog and answer the query using that catalog."""
        try:
            print(f"\n=== ORCHESTRATOR PROCESSING ===")
            print(f"Query: {query}")
            
            # Find the most relevant catalog with improved search
            relevant_catalogs = self.catalog_library.search_relevant_catalogs(query, self.processor, top_k=3)
            
            if not relevant_catalogs:
                return "No suitable catalog found for your query."
            
            best_catalog, score = relevant_catalogs[0]
            print(f"Selected catalog: {best_catalog} with score: {score}")
            
            # If the best score is too low, try searching all catalogs
            if score < 4.0:
                print(f"Low relevance score ({score}), trying all catalogs...")
                # Try with the second best catalog if available
                if len(relevant_catalogs) > 1:
                    second_best, second_score = relevant_catalogs[1]
                    if second_score > score:
                        best_catalog, score = second_best, second_score
                        print(f"Using second choice: {best_catalog} with score: {second_score}")
            
            # Get the specialized catalog agent
            catalog_agent = await self.multi_system.get_catalog_agent(best_catalog)
            
            # Get the detailed response from the catalog agent
            detailed_response = await catalog_agent.chat_response(query)
            
            # If the response indicates no match, try other catalogs
            if ("no information" in detailed_response.lower() and "temperature glass kettle" in query.lower()) or \
               ("sorry" in detailed_response.lower() and "not" in detailed_response.lower()):
                print("Primary catalog didn't have relevant info, trying other catalogs...")
                
                for catalog_name, catalog_score in relevant_catalogs[1:]:
                    print(f"Trying backup catalog: {catalog_name}")
                    backup_agent = await self.multi_system.get_catalog_agent(catalog_name)
                    backup_response = await backup_agent.chat_response(query)
                    
                    # If this catalog has better information, use it
                    if not ("no information" in backup_response.lower() and "sorry" in backup_response.lower()):
                        best_catalog = catalog_name
                        score = catalog_score
                        detailed_response = backup_response
                        break
            
            # Format the final response
            result = f"**Selected Catalog: {best_catalog}** (Relevance: {score}/10)\n\n"
            result += f"**Answer:**\n{detailed_response}"
            
            return result
            
        except Exception as e:
            print(f"Error in orchestrator: {str(e)}")
            return f"Error processing query: {str(e)}"
    
    async def search_catalogs(self, query: str) -> str:
        """Search for relevant catalogs based on user query."""
        try:
            relevant_catalogs = self.catalog_library.search_relevant_catalogs(query, self.processor, top_k=5)
            
            if not relevant_catalogs:
                return "No catalogs found matching your query."
            
            result = f"Found {len(relevant_catalogs)} relevant catalogs for your query:\n\n"
            
            for i, (catalog_name, score) in enumerate(relevant_catalogs, 1):
                metadata = self.catalog_library.catalogs[catalog_name]
                result += f"{i}. **{catalog_name}** (Relevance: {score}/10)\n"
                result += f"   Summary: {metadata.summary}\n"
                result += f"   Categories: {', '.join(metadata.categories)}\n"
                result += f"   Pages: {metadata.page_count}\n\n"
            
            return result
            
        except Exception as e:
            return f"Error searching catalogs: {str(e)}"
    
    async def get_catalog_overview(self) -> str:
        """Get overview of all available catalogs."""
        try:
            if not self.catalog_library.catalogs:
                return "No catalogs available in the library."
            
            overview = f"**Catalog Library Overview**\n\n"
            overview += f"Total Catalogs: {len(self.catalog_library.catalogs)}\n\n"
            
            for filename, metadata in self.catalog_library.catalogs.items():
                overview += f"📄 **{filename}**\n"
                overview += f"   • {metadata.summary}\n"
                overview += f"   • Categories: {', '.join(metadata.categories)}\n"
                overview += f"   • Product Types: {', '.join(metadata.product_types)}\n"
                overview += f"   • Pages: {metadata.page_count}\n\n"
            
            return overview
            
        except Exception as e:
            return f"Error getting catalog overview: {str(e)}"

class CatalogTools:
    """Tools for the individual catalog agent."""
    
    def __init__(self, catalog_data: str, pdf_images: List[Image.Image], processor: PDFCatalogProcessor, catalog_name: str):
        self.catalog_data = catalog_data
        self.pdf_images = pdf_images
        self.processor = processor
        self.catalog_name = catalog_name
    
    async def search_products(self, query: str) -> str:
        """Search for products in the catalog based on query."""
        try:
            print(f"\n=== CATALOG AGENT SEARCH ===")
            print(f"Catalog: {self.catalog_name}")
            print(f"Query: {query}")
            print(f"Catalog data preview: {self.catalog_data[:500]}...")
            
            search_prompt = f"""
            You are analyzing the catalog "{self.catalog_name}" for products related to "{query}".
            
            Catalog content:
            {self.catalog_data[:12000]}  # Increased context window
            
            TASK: Search thoroughly for ANY products that match or relate to the query "{query}".
            
            If you find matching products, provide:
            1. All matching products with full details
            2. Exact product names and model numbers
            3. Prices and specifications
            4. Page numbers where found
            5. Why each product matches the search
            6. Features and capabilities
            7. Warranty and support info
            
            If NO matching products are found, respond with:
            "No products matching '{query}' were found in this catalog. This catalog contains [list the main product types you can see]."
            
            Be thorough and accurate. Don't make up information.
            """
            
            response = self.processor.model.generate_content(search_prompt)
            result = response.text
            print(f"Search result: {result[:200]}...")
            return result
            
        except Exception as e:
            return f"Error searching products in {self.catalog_name}: {str(e)}"
    
    async def get_product_details(self, product_name: str) -> str:
        """Get detailed information about a specific product."""
        try:
            detail_prompt = f"""
            From catalog {self.catalog_name}, find detailed information about "{product_name}":
            
            {self.catalog_data[:8000]}
            
            Provide complete details including:
            - Full product name and model
            - All specifications and features
            - Price and pricing options
            - Page location
            - Category/section
            - Related products
            - Availability information
            
            If exact product not found, suggest closest matches.
            """
            
            response = self.processor.model.generate_content(detail_prompt)
            return response.text
            
        except Exception as e:
            return f"Error getting product details: {str(e)}"
    
    async def compare_products(self, product1: str, product2: str) -> str:
        """Compare two products from the catalog."""
        try:
            compare_prompt = f"""
            From catalog {self.catalog_name}, compare "{product1}" and "{product2}":
            
            {self.catalog_data[:8000]}
            
            Provide:
            1. Side-by-side comparison table
            2. Price comparison
            3. Feature differences
            4. Pros and cons for each
            5. Recommendations for different use cases
            6. Page references
            
            If products not found, suggest similar alternatives.
            """
            
            response = self.processor.model.generate_content(compare_prompt)
            return response.text
            
        except Exception as e:
            return f"Error comparing products: {str(e)}"
    
    async def analyze_specific_pages(self, page_numbers: str, focus: str = "general analysis") -> str:
        """Analyze specific pages with focused attention."""
        try:
            pages = [int(p.strip()) for p in page_numbers.split(',') if p.strip().isdigit()]
            valid_pages = [i-1 for i in pages if 0 < i <= len(self.pdf_images)]
            
            if not valid_pages:
                return "No valid page numbers provided. Please specify page numbers separated by commas."
            
            pages_to_analyze = [self.pdf_images[i] for i in valid_pages]
            
            analyze_prompt = f"""
            Analyze pages {page_numbers} from catalog {self.catalog_name} with focus on: {focus}
            
            Extract:
            1. All products on these pages
            2. Complete text content
            3. Pricing and specifications
            4. Special offers or promotions
            5. Technical details
            6. Contact/ordering information
            
            Focus area: {focus}
            Be thorough and extract all visible text.
            """
            
            response = self.processor.model.generate_content([analyze_prompt] + pages_to_analyze)
            return response.text
            
        except Exception as e:
            return f"Error analyzing pages: {str(e)}"
    
    async def get_catalog_overview(self) -> str:
        """Get overview of the catalog."""
        try:
            overview_prompt = f"""
            Provide a comprehensive overview of catalog {self.catalog_name}:
            
            {self.catalog_data[:8000]}
            
            Include:
            1. Business type and product categories
            2. Total number of products
            3. Price ranges
            4. Main sections/categories  
            5. Special features or highlights
            6. Contact and ordering information
            7. List of main product names/types available
            
            Keep it informative but concise.
            """
            
            response = self.processor.model.generate_content(overview_prompt)
            return response.text
            
        except Exception as e:
            return f"Error generating overview: {str(e)}"

class OrchestratorAgent:
    """Orchestrator agent that selects appropriate catalogs and answers queries."""
    
    def __init__(self, gemini_api_key: str, openai_client: AsyncOpenAI, catalog_library: CatalogLibrary, multi_system):
        self.processor = PDFCatalogProcessor(gemini_api_key)
        self.openai_client = openai_client
        self.catalog_library = catalog_library
        self.multi_system = multi_system  # Reference to MultiCatalogSystem
        self.tools = OrchestratorTools(catalog_library, self.processor, multi_system)
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the orchestrator agent."""
        catalog_summary = self.catalog_library.get_catalog_summaries()
        print(f"\n=== ORCHESTRATOR INITIALIZATION ===")
        print(f"Available catalogs summary:\n{catalog_summary}")
        
        self.agent = agents.Agent(
            name="Catalog Orchestrator",
            instructions=f"""
            You are the Catalog Orchestrator Agent. Your primary job is to answer user questions by:
            1. Selecting the most relevant catalog for the user's query
            2. Using that catalog to provide detailed answers

            For ANY product-related question, use the "answer_query_with_best_catalog" tool which will:
            - Find the most relevant catalog based on product types, categories, and keywords
            - Get detailed information from that catalog
            - Return a comprehensive answer

            Available Catalogs:
            {catalog_summary}

            When a user asks about products, features, specifications, prices, or any catalog-related information:
            - ALWAYS use the answer_query_with_best_catalog tool first
            - This tool will automatically select the best catalog and provide the detailed answer
            - The tool includes fallback logic to try multiple catalogs if needed
            - Do not use other tools unless specifically asked for catalog overviews or searches

            Be helpful and conversational, but always rely on the tools to provide accurate information.
            Focus on getting the best possible answer from the most relevant catalog.
            """,
            tools=[
                agents.function_tool(self.tools.answer_query_with_best_catalog),
                agents.function_tool(self.tools.search_catalogs),
                agents.function_tool(self.tools.get_catalog_overview),
            ],
            model=agents.OpenAIChatCompletionsModel(
                model=AGENT_LLM_NAME,
                openai_client=self.openai_client
            ),
        )
    
    async def chat_response(self, question: str) -> Tuple[str, Optional[str]]:
        if not self.agent:
            return "❌ Orchestrator not initialized.", None

        try:
            print(f"\n=== ORCHESTRATOR CHAT ===")
            print(f"Question: {question}")
            
            result = await agents.Runner.run(self.agent, input=question)
            print("DEBUG: Agent result:", result)

            # Extract the response text
            response_text = ""
            if hasattr(result, 'messages') and result.messages:
                for message in reversed(result.messages):
                    if hasattr(message, 'role') and message.role == 'assistant':
                        if hasattr(message, 'content'):
                            if isinstance(message.content, str) and message.content.strip():
                                response_text = message.content
                                break
                            elif isinstance(message.content, list):
                                text_parts = []
                                for content_block in message.content:
                                    if hasattr(content_block, 'text') and content_block.text.strip():
                                        text_parts.append(content_block.text)
                                if text_parts:
                                    response_text = ' '.join(text_parts)
                                    break

            # Fallback handling
            if not response_text and hasattr(result, 'output') and result.output:
                response_text = str(result.output)
            if not response_text and hasattr(result, 'final_output') and result.final_output:
                response_text = str(result.final_output)

            # Try to identify which catalog was selected
            selected_catalog = None
            if "Selected Catalog:" in response_text:
                for catalog_name in self.catalog_library.catalogs.keys():
                    if catalog_name in response_text:
                        selected_catalog = catalog_name
                        break

            return response_text or "No response from agent.", selected_catalog

        except Exception as e:
            print(f"Error in orchestrator chat: {str(e)}")
            return f"Error from orchestrator: {str(e)}", None

class PDFCatalogAgent:
    """Individual catalog agent."""
    
    def __init__(self, gemini_api_key: str, openai_client: AsyncOpenAI, catalog_name: str):
        self.processor = PDFCatalogProcessor(gemini_api_key)
        self.openai_client = openai_client
        self.catalog_name = catalog_name
        self.catalog_data = ""
        self.pdf_images = []
        self.tools = None
        self.agent = None
        
    async def initialize_catalog(self, pdf_path: str) -> None:
        """Initialize catalog by processing PDF."""
        try:
            print(f"🔄 Processing PDF catalog: {self.catalog_name}...")
            
            # Convert PDF to images
            self.pdf_images = self.processor.pdf_to_images(pdf_path)
            print(f"✅ Converted {len(self.pdf_images)} pages to images")
            
            # Analyze catalog in batches
            print("🔄 Analyzing catalog content...")
            batch_size = 10  # Reduced batch size for better analysis
            all_analyses = []
            
            for i in range(0, len(self.pdf_images), batch_size):
                batch = self.pdf_images[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(self.pdf_images) + batch_size - 1) // batch_size
                
                print(f"Analyzing batch {batch_num}/{total_batches} ({len(batch)} pages)...")
                analysis = self.processor.analyze_catalog_batch(batch, i)
                all_analyses.append(f"=== PAGES {i+1}-{min(i+batch_size, len(self.pdf_images))} ===\n{analysis}")
            
            # Combine analyses
            full_analysis = "\n\n".join(all_analyses)
            
            # Create consolidated summary with enhanced product extraction
            consolidation_prompt = f"""
            Create a consolidated, well-organized, and highly searchable knowledge base for catalog {self.catalog_name}.
            
            IMPORTANT REQUIREMENTS:
            1. Extract ALL product names, models, and variations
            2. Create a comprehensive product index at the beginning
            3. Organize by categories and product types
            4. Include ALL specifications, prices, and features
            5. Remove duplicates but keep all unique information
            6. Make it easily searchable for any product query
            
            Original Analysis:
            {full_analysis[:20000]}  # Increased limit for better consolidation
            
            Format as:
            === PRODUCT INDEX ===
            [List all products found with page references]
            
            === DETAILED CATALOG CONTENT ===
            [Organized, searchable content]
            """
            
            print("Creating consolidated catalog knowledge base...")
            consolidated_response = self.processor.model.generate_content(consolidation_prompt)
            self.catalog_data = consolidated_response.text
            
            print(f"Catalog data preview for {self.catalog_name}:")
            print(self.catalog_data[:1000])
            
            # Initialize tools and agent
            self.tools = CatalogTools(self.catalog_data, self.pdf_images, self.processor, self.catalog_name)
            
            # Create OpenAI Agent
            self.agent = agents.Agent(
                name=f"PDF Catalog Assistant - {self.catalog_name}",
                instructions=f"""
                You are an expert product catalog assistant with comprehensive knowledge of the catalog: {self.catalog_name}
                
                You have access to the following tools:
                - search_products: Search for products by name, category, features, or price
                - get_product_details: Get detailed information about specific products
                - compare_products: Compare two products side by side
                - analyze_specific_pages: Analyze specific pages with focused attention
                - get_catalog_overview: Get an overview of the entire catalog
                
                Catalog Overview:
                {self.catalog_data[:3000]}...
                
                Your primary responsibilities:
                1. Answer questions about ANY product in this catalog
                2. Search and recommend products based on customer needs
                3. Provide detailed specifications and pricing
                4. Compare products and make recommendations
                5. Analyze specific pages for detailed information
                6. Help with product selection and purchasing decisions
                
                IMPORTANT GUIDELINES:
                - Always use the search_products tool for any product-related query
                - Be thorough in your searches - check for variations, similar products, and related items
                - If you don't find an exact match, look for similar or related products
                - Always mention the catalog name: {self.catalog_name}
                - Be helpful and accurate, referencing specific page numbers when available
                - If no products match the query, clearly state what products ARE available in this catalog
                
                Be conversational and friendly while providing comprehensive answers.
                """,
                tools=[
                    agents.function_tool(self.tools.search_products),
                    agents.function_tool(self.tools.get_product_details),
                    agents.function_tool(self.tools.compare_products),
                    agents.function_tool(self.tools.analyze_specific_pages),
                    agents.function_tool(self.tools.get_catalog_overview),
                ],
                model=agents.OpenAIChatCompletionsModel(
                    model=AGENT_LLM_NAME, 
                    openai_client=self.openai_client
                ),
            )
            
            print(f"✅ Catalog {self.catalog_name} initialized! {len(self.pdf_images)} pages processed.")
            
        except Exception as e:
            raise Exception(f"Error initializing catalog {self.catalog_name}: {str(e)}")
    
    async def chat_response(self, question: str) -> str:
        """Get chat response using OpenAI Agent SDK."""
        if not self.agent:
            return f"❌ Catalog {self.catalog_name} not initialized."
            
        try:
            print(f"\n=== CATALOG AGENT RESPONSE ===")
            print(f"Catalog: {self.catalog_name}")
            print(f"Question: {question}")
            
            result = await agents.Runner.run(self.agent, input=question)
            print("DEBUG: Agent result:", result)
            
            # Extract the final response
            if hasattr(result, 'messages') and result.messages:
                for message in reversed(result.messages):
                    if hasattr(message, 'role') and message.role == 'assistant':
                        if hasattr(message, 'content'):
                            if isinstance(message.content, str):
                                return message.content
                            elif isinstance(message.content, list):
                                text_parts = []
                                for content_block in message.content:
                                    if hasattr(content_block, 'text'):
                                        text_parts.append(content_block.text)
                                if text_parts:
                                    return ' '.join(text_parts)
            
            # Fallback handling
            print("Using fallback search...")
            return await self.tools.search_products(question)
                    
        except Exception as e:
            print(f"Chat response error for {self.catalog_name}: {str(e)}")
            try:
                return await self.tools.search_products(question)
            except Exception as tool_error:
                return f"I encountered an error processing your request in {self.catalog_name}: {str(e)}. Please try rephrasing your question."

class MultiCatalogSystem:
    """Main system that manages orchestrator and individual catalog agents."""
    
    def __init__(self, gemini_api_key: str, openai_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.catalog_library = CatalogLibrary()
        self.catalog_library._load_metadata()  # Load existing metadata
        self.orchestrator = OrchestratorAgent(gemini_api_key, self.openai_client, self.catalog_library, self)
        self.catalog_agents: Dict[str, PDFCatalogAgent] = {}
        
    async def add_catalog(self, pdf_file) -> str:
        """Add a new catalog to the system."""
        try:
            # Add to library and get metadata
            metadata = self.catalog_library.add_catalog(pdf_file, self.orchestrator.processor)
            
            # Print debug info about the added catalog
            print(f"\n=== CATALOG ADDED ===")
            print(f"Filename: {metadata.filename}")
            print(f"Summary: {metadata.summary}")
            print(f"Categories: {metadata.categories}")
            print(f"Product Types: {metadata.product_types}")
            print(f"Keywords: {metadata.keywords}")
            
            # Reinitialize orchestrator with updated catalog info
            self.orchestrator._initialize_agent()
            
            return f"✅ Successfully added catalog: {metadata.filename}"
            
        except Exception as e:
            return f"❌ Error adding catalog: {str(e)}"
    
    async def get_catalog_agent(self, catalog_name: str) -> PDFCatalogAgent:
        """Get or create a catalog agent for specific catalog."""
        if catalog_name not in self.catalog_agents:
            if catalog_name not in self.catalog_library.catalogs:
                raise Exception(f"Catalog {catalog_name} not found in library")
            
            print(f"Creating new agent for catalog: {catalog_name}")
            # Create new agent
            agent = PDFCatalogAgent(self.gemini_api_key, self.openai_client, catalog_name)
            catalog_path = self.catalog_library.catalogs[catalog_name].file_path
            
            # Initialize the agent with the catalog
            await agent.initialize_catalog(catalog_path)
            
            # Store the agent
            self.catalog_agents[catalog_name] = agent
        
        return self.catalog_agents[catalog_name]
    
    async def process_query(self, question: str) -> str:
        """Process a user query using the orchestrator agent."""
        try:
            print(f"\n=== SYSTEM QUERY PROCESSING ===")
            print(f"Available catalogs: {list(self.catalog_library.catalogs.keys())}")
            print(f"Question: {question}")
            
            # The orchestrator will now automatically select the best catalog and get the answer
            orchestrator_response, selected_catalog = await self.orchestrator.chat_response(question)
            return orchestrator_response
        except Exception as e:
            print(f"Error in system query processing: {str(e)}")
            return f"❌ Error processing query: {str(e)}"

# Streamlit App Configuration
st.set_page_config(
    page_title="Multi-PDF Catalog System with Orchestrator Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def create_streamlit_app():
    """Create Streamlit interface for the multi-PDF catalog system."""
    
    # Title and description
    st.title("🤖 Multi-PDF Catalog System with Orchestrator Agent")
    st.markdown("Upload multiple product catalog PDFs and chat with an AI orchestrator that selects the most appropriate catalog for your queries!")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Keys
        st.subheader("API Keys")
        
        # Check for environment variables first
        gemini_key_env = os.getenv("GEMINI_API_KEY")
        openai_key_env = os.getenv("OPENAI_API_KEY")
        
        if gemini_key_env:
            st.success("✅ Gemini API key loaded from environment")
            gemini_api_key = gemini_key_env
        else:
            gemini_api_key = st.text_input(
                "Gemini API Key",
                type="password",
                help="Get your API key from https://makersuite.google.com/app/apikey",
                placeholder="Enter your Gemini API key..."
            )
        
        if openai_key_env:
            st.success("✅ OpenAI API key loaded from environment")
            openai_api_key = openai_key_env
        else:
            openai_api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="Get your API key from https://platform.openai.com/api-keys",
                placeholder="Enter your OpenAI API key..."
            )
        
        if not gemini_api_key or not openai_api_key:
            st.warning("⚠️ Please provide both API keys to continue.")
            st.stop()
        
        st.divider()
        
        # File upload section
        st.subheader("📄 PDF Upload")
        uploaded_files = st.file_uploader(
            "Upload PDF Catalogs",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload multiple product catalog PDF files (max 300 PDFs)"
        )
        
        if uploaded_files:
            st.success(f"📄 {len(uploaded_files)} PDF(s) selected")
            total_size = sum(file.size for file in uploaded_files) / 1024 / 1024
            st.info(f"Total size: {total_size:.1f} MB")
            
            # Show list of uploaded files
            with st.expander("📋 Uploaded Files", expanded=False):
                for i, file in enumerate(uploaded_files, 1):
                    st.write(f"{i}. {file.name} ({file.size / 1024 / 1024:.1f} MB)")
        
        st.divider()
        
        # System status
        if 'multi_system' in st.session_state and st.session_state.multi_system:
            st.subheader("📊 System Status")
            catalog_count = len(st.session_state.multi_system.catalog_library.catalogs)
            st.metric("Catalogs Loaded", catalog_count)
            st.metric("Active Agents", len(st.session_state.multi_system.catalog_agents))
            
            if catalog_count > 0:
                if st.button("🔄 Refresh Orchestrator", use_container_width=True):
                    st.session_state.multi_system.orchestrator._initialize_agent()
                    st.success("Orchestrator refreshed!")
                    st.rerun()
                
                # Show catalog summaries for debugging
                with st.expander("🔍 Debug: Catalog Details", expanded=False):
                    for name, metadata in st.session_state.multi_system.catalog_library.catalogs.items():
                        st.write(f"**{name}**")
                        st.write(f"Summary: {metadata.summary}")
                        st.write(f"Categories: {metadata.categories}")
                        st.write(f"Product Types: {metadata.product_types}")
                        st.write(f"Keywords: {metadata.keywords}")
                        st.write("---")
        
        st.divider()
        
        # Quick actions
        if 'multi_system' in st.session_state and st.session_state.multi_system:
            st.subheader("🚀 Quick Actions")
            
            if st.button("📋 Library Overview", use_container_width=True):
                st.session_state.quick_action = "library_overview"
                st.rerun()
            
            if st.button("🔍 Search All Catalogs", use_container_width=True):
                st.session_state.quick_action = "search_all"
                st.rerun()
            
            if st.button("💡 Get Recommendations", use_container_width=True):
                st.session_state.quick_action = "recommendations"
                st.rerun()
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'multi_system' not in st.session_state:
        st.session_state.multi_system = None
    
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()
    
    # Initialize system if not already done
    if st.session_state.multi_system is None:
        try:
            st.session_state.multi_system = MultiCatalogSystem(gemini_api_key, openai_api_key)
            if not st.session_state.messages:
                welcome_msg = """Hello! I'm your Multi-Catalog Orchestrator Agent. I can help you navigate through multiple product catalogs.

**How it works:**
1. Upload your PDF catalogs (up to 300 PDFs)
2. I'll analyze each catalog and understand what products they contain
3. When you ask questions, I'll automatically select the most relevant catalog and provide detailed answers

**What you can ask:**
- "What information do you have on programmable coffee makers?"
- "Show me kitchen appliances under $200"
- "What's the name of the coffee machine in the manual?"
- "Compare different laptop models"

Upload your catalogs to get started!"""
                st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
        except Exception as e:
            st.error(f"❌ Error initializing system: {str(e)}")
            st.stop()
    
    # Handle file uploads
    if uploaded_files:
        new_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files]
        
        if new_files:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, file in enumerate(new_files):
                status_text.text(f"Processing {file.name}... ({i+1}/{len(new_files)})")
                progress_bar.progress((i) / len(new_files))
                
                try:
                    result = asyncio.run(
                        st.session_state.multi_system.add_catalog(file)
                    )
                    st.session_state.processed_files.add(file.name)
                    
                except Exception as e:
                    st.error(f"❌ Error processing {file.name}: {str(e)}")
                    continue
            
            progress_bar.progress(1.0)
            status_text.text("✅ All files processed!")
            
            # Update messages
            catalog_count = len(st.session_state.multi_system.catalog_library.catalogs)
            success_msg = f"✅ Successfully processed {len(new_files)} new catalog(s)! Total catalogs: {catalog_count}"
            st.session_state.messages.append({"role": "assistant", "content": success_msg})
            
            # Clear progress indicators after a moment
            import time
            time.sleep(2)
            progress_bar.empty()
            status_text.empty()
            
            st.rerun()
    
    # Handle quick actions
    if 'quick_action' in st.session_state and st.session_state.multi_system:
        quick_questions = {
            "library_overview": "Give me an overview of all available catalogs in the library",
            "search_all": "What types of products are available across all catalogs?",
            "recommendations": "What are some popular or featured products across the catalogs?"
        }
        
        question = quick_questions.get(st.session_state.quick_action)
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            
            with st.spinner("🤔 Processing quick action..."):
                try:
                    response = asyncio.run(
                        st.session_state.multi_system.process_query(question)
                    )
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})
        
        # Clear quick action
        del st.session_state.quick_action
        st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat with Your Catalog Library")
        
        # Chat history container
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Chat input
        if st.session_state.multi_system:
            if prompt := st.chat_input("Ask about products across any catalog, or request specific comparisons..."):
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Get and display assistant response
                with st.chat_message("assistant"):
                    with st.spinner("🤔 Analyzing query, selecting best catalog, and generating response..."):
                        try:
                            response = asyncio.run(
                                st.session_state.multi_system.process_query(prompt)
                            )
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        except Exception as e:
                            error_msg = f"Sorry, I encountered an error: {str(e)}"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            st.info("👆 System initializing... Please wait.")
    
    with col2:
        st.subheader("📚 Catalog Library")
        
        if st.session_state.multi_system and st.session_state.multi_system.catalog_library.catalogs:
            for filename, metadata in st.session_state.multi_system.catalog_library.catalogs.items():
                with st.expander(f"📄 {filename}", expanded=False):
                    st.write(f"**Summary:** {metadata.summary}")
                    st.write(f"**Categories:** {', '.join(metadata.categories)}")
                    st.write(f"**Product Types:** {', '.join(metadata.product_types)}")
                    st.write(f"**Keywords:** {', '.join(metadata.keywords)}")
                    st.write(f"**Pages:** {metadata.page_count}")
                    
                    if st.button(f"Ask about {filename}", key=f"ask_{filename}"):
                        question = f"What products are available in {filename}?"
                        st.session_state.messages.append({"role": "user", "content": question})
                        st.rerun()
        else:
            st.info("No catalogs loaded yet. Upload PDF files to see them here.")
        
        st.divider()
        
        # System statistics
        if st.session_state.multi_system:
            st.subheader("📊 Statistics")
            catalog_count = len(st.session_state.multi_system.catalog_library.catalogs)
            agent_count = len(st.session_state.multi_system.catalog_agents)
            message_count = len(st.session_state.messages)
            
            col_a, col_b = st.columns(2)
            col_a.metric("Catalogs", catalog_count)
            col_b.metric("Agents", agent_count)
            st.metric("Messages", message_count)
    
    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
    
    # Example questions
    if st.session_state.multi_system and st.session_state.multi_system.catalog_library.catalogs:
        with st.expander("💡 Example Questions", expanded=False):
            examples = [
                "What information do you have on Temperature Glass Kettle?",
                "Show me all kettles available",
                "What coffee makers do you have?",
                "Find me wireless headphones under $100",
                "What kitchen appliances are available?",
                "Compare different espresso machines",
                "Show me products on sale or discounted",
                "What's the most expensive item across all catalogs?",
                "Find eco-friendly products",
                "What electronics are available?"
            ]
            
            cols = st.columns(2)
            for i, example in enumerate(examples):
                col = cols[i % 2]
                if col.button(example, key=f"example_{i}"):
                    st.session_state.messages.append({"role": "user", "content": example})
                    with st.spinner("Processing..."):
                        try:
                            response = asyncio.run(
                                st.session_state.multi_system.process_query(example)
                            )
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.rerun()
                        except Exception as e:
                            st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})
                            st.rerun()
    
    # Features showcase (when no catalogs loaded)
    if not st.session_state.multi_system or not st.session_state.multi_system.catalog_library.catalogs:
        st.markdown("---")
        st.subheader("🚀 System Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🧠 Smart Orchestrator
            - Automatically selects best catalog
            - Understands query context
            - Routes to specialized agents
            - Provides comprehensive answers
            """)
        
        with col2:
            st.markdown("""
            ### 📚 Multi-Catalog Management
            - Support for up to 300 PDFs
            - Automatic metadata generation
            - Smart catalog categorization
            - Persistent storage system
            """)
        
        with col3:
            st.markdown("""
            ### 🔍 Advanced Search
            - Cross-catalog product search
            - Semantic understanding
            - Product comparisons
            - Contextual recommendations
            """)
        
        st.markdown("---")
        st.subheader("📋 How It Works")
        st.markdown("""
        1. **Upload Catalogs**: Add multiple PDF catalogs to your library
        2. **Automatic Processing**: Each catalog is analyzed and categorized
        3. **Smart Query Processing**: Ask any question and the system automatically:
           - Selects the most relevant catalog
           - Uses specialized agent to analyze that catalog
           - Provides detailed, accurate answers
        4. **Seamless Experience**: Get comprehensive responses without manual catalog selection
        """)

# Run the Streamlit app
if __name__ == "__main__":
    # Disable OpenAI agents tracing
    agents.set_tracing_disabled(disabled=True)
    
    # Create and run the Streamlit app
    create_streamlit_app()