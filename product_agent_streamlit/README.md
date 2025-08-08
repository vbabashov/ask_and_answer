# Product Agent Streamlit

## Overview

The **Product Agent Streamlit** application is a multi-catalog search tool that allows users to upload product catalogs (PDFs) and search across them for detailed product information. It uses a combination of OpenAI Agents, Google Gemini AI, and PDF processing to provide accurate and structured responses to user queries.

## Features

1. **Upload and Manage Catalogs**:
  - Upload multiple PDF catalogs via the sidebar.
  - Automatically processes and extracts content from the uploaded PDFs.
  - Summarizes catalogs for quick reference.

2. **Search Across Catalogs**:
  - Enter a query in the search bar to find relevant information across all uploaded catalogs.
  - Uses AI agents to provide structured and accurate responses.

3. **Catalog Summaries**:
  - View summaries of all uploaded catalogs in a structured format.

## Prerequisites

- **Python**: Version 3.10 or higher.
- **API Keys**:
 - `GEMINI_API_KEY`: For Google Gemini AI.
 - `OPENAI_API_KEY`: For OpenAI Agents.
- **Dependencies**: Listed in `requirements.txt`.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ask_and_answer/product_agent_streamlit
```

### 2. Create a Virtual Environment
```
python -m venv .venv
```
### 3. Activate the Virtual Environment

Windows:
```
.venv\Scripts\activate
```

### 4. Install Dependencies
```
pip install -r requirements.txt
```
### 5. Set Up Environment Variables


Create a .env file in the product_agent_streamlit directory with the following content:

```
OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
OPENAI_API_KEY="your_openai_api_key_here"
GEMINI_API_KEY="your_gemini_api_key_here"
```

Replace your_openai_api_key_here and your_gemini_api_key_here with your actual API keys.
Running the Application

Activate the virtual environment (if not already activated):

Windows:
```
.venv\Scripts\activate
```

Run the Streamlit app:
```
streamlit run main.py
```

Open the app in your browser:

Local URL: http://localhost:8501
Network URL: Provided in the terminal output.


## Features in Detail
### 1. Upload and Manage Catalogs

Upload multiple PDF catalogs via the sidebar.
Automatically processes and extracts content from the uploaded PDFs.
Summarizes catalogs for quick reference.

### 2. Search Across Catalogs

Enter a query in the search bar to find relevant information across all uploaded catalogs.
Uses AI agents to provide structured and accurate responses.

### 3. Catalog Summaries

View summaries of all uploaded catalogs in a structured format.

Key Components
#### 1. MultiCatalogSystem

Manages the overall system, including catalog uploads, AI agent interactions, and query handling.

#### 2. Custom Agents

OrchestratorAgent: Selects the most relevant catalog for a given query.
CatalogAgent: Extracts detailed information from a specific catalog.

#### 3. Processors

PDFProcessor: Converts PDFs to images, extracts content, and generates summaries.
CatalogManager: Manages catalog metadata and content.

## Usage

* **Upload Catalogs** : Use the sidebar to upload PDF catalogs.
* **Search Products**: Enter your query in the search bar to find product information.
* **View Results**: The application will automatically select the most relevant catalog and provide detailed information.
* **Browse Summaries**: Click "Show All Catalog Summaries" to view an overview of all uploaded catalogs.