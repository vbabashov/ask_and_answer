# Ask and Answer Project

## Overview

This is a customer service chatbot with Reason-and-Act multi-agent design addressing a wide range of customer pre- and post- purchase queries about products available for sale the on Canadian Tire Website.

## Setup

1. **Clone the repository**
   ```sh
   git clone <your-repo-url>
   cd ask_and_answer
   ```

2. **Install dependencies**
   - Ensure you have Python 3.8+ and [uv](https://github.com/astral-sh/uv) installed.
   - Install dependencies:
     ```sh
     uv sync
     ```

3. **Environment Variables**
   - Ensure all environment variables and certificate paths are set in `.env` file.


## Running Connection Tests

To run the test scripts:
```sh
uv run test_embedding.py
uv run test_llm_agent.py
```

## Requirements

- LLM: gpt-4o 
- Embeddings: text-embedding-ada-002
- Framework: OpenAI Agents SDK
- Observability/Tracing: Langfuse
- Long-Term Memory: MongoDB
- Evals: TBD
- Demo: Gradio



