
from src.embeddings import aoai_embed_query
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import os
from dotenv import load_dotenv
load_dotenv()

def main():
    
    token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    user_message = "What is the capital of France?"
    client = AzureOpenAI(
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_ad_token_provider=token_provider,
        )
    embedded_query_results = aoai_embed_query(query=user_message, client=client)
    print(f"Embedded query: {embedded_query_results}")


if __name__ == "__main__":
    main()