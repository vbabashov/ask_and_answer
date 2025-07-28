import re
import os
import asyncio

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI, AsyncAzureOpenAI
from openai.types.responses import ResponseTextDeltaEvent
from agents import set_default_openai_client,set_default_openai_api,set_tracing_disabled
from agents import add_trace_processor
from agents.tracing.processors import ConsoleSpanExporter, BatchTraceProcessor
from agents import Agent, OpenAIChatCompletionsModel, function_tool, Runner, ItemHelpers, RunContextWrapper

from src.utils.azure_openai.client import get_openai_client

from dotenv import load_dotenv
load_dotenv()

# client = AzureOpenAI(
#     api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
#     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
#     azure_ad_token_provider=token_provider,
# )

# # chat completion 
# chat_completion = client.chat.completions.create(
#     model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
#      messages=[
#         {
#             "role": "system",
#             "content": "You are a helpful assistant.",
#         },
#         {
#             "role": "user",
#             "content": "I am going to Paris, what should I see?",
#         }
#     ],
#     temperature=0,
#     max_tokens=4096,
# )
# response = chat_completion.choices[0].message.content

# print(response)

async def main():

    # Initialize the Azure OpenAI client
    openai_client = get_openai_client()

    # Set the default OpenAI client for the Agents SDK at the global level once
    set_default_openai_client(openai_client)
    set_default_openai_api ("chat_completions")
    set_tracing_disabled(True)

    agent = Agent(
        name="Explorer Agent",
        instructions="You are an explorer agent which helps in finding information about places.",
        # model = OpenAIChatCompletionsModel(openai_client=openai_client,
        #     model=os.getenv("AZURE_OPENAI_DEPLOYMENT"))
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT")
    )

    response = await Runner.run(agent, "I am going to Paris, what should I see?")
    print(response.final_output)


if __name__ == "__main__":
    asyncio.run(main())
