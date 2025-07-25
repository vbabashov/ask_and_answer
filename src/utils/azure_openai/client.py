from azure.identity import DefaultAzureCredential
from azure.identity import get_bearer_token_provider
from openai import AzureOpenAI
import os


def get_openai_client():
    """
    Retrieves Azure OpenAI Client
    """
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=token_provider,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    return client