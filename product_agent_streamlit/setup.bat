@echo off
REM Exit immediately if a command fails
setlocal enabledelayedexpansion
set "ERRORLEVEL=0"

REM Step 1: Create the .env file
echo Creating .env file...
(
    echo OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
    echo OPENAI_API_KEY="your_openai_api_key_here"
    echo GEMINI_API_KEY="your_gemini_api_key_here"
) > product_agent_streamlit\.env
echo .env file created successfully.

REM Step 2: Check if 'uv' is installed
echo Checking if 'uv' is installed...
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 'uv' is not installed. Installing 'uv'...
    pip install uv
) else (
    echo 'uv' is already installed.
)

REM Step 3: Install dependencies using 'uv'
echo Installing dependencies from requirements.txt...
cd product_agent_streamlit
uv sync requirements.txt

REM Step 4: Activate the environment
echo Activating the environment...
call .venv\Scripts\activate

REM Step 5: Run the Streamlit app
echo Running the Streamlit app...
cd product_agent_streamlit
python -m streamlit run main.py
