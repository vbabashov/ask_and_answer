# Ask and Answer Project

## Overview

This is a customer service chatbot with multi-agent design addressing a wide range of customer pre- and post- purchase queries about products on Canadian Tire Website.

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


## Running Tests

To run the test scripts:
```sh
uv run test_embedding.py
uv run test_llm_agent.py
```

## Requirements

- OpenAI Agents SDK
- Langfuse
- Gradio
- MongoDB



