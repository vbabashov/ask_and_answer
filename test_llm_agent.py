import re
import os
import asyncio

from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from openai import AzureOpenAI
from openai import AsyncAzureOpenAI
from openai.types.responses import ResponseTextDeltaEvent
from agents import set_default_openai_client,set_default_openai_api,set_tracing_disabled
from agents import add_trace_processor
from agents.tracing.processors import ConsoleSpanExporter, BatchTraceProcessor
from agents import Agent, OpenAIChatCompletionsModel, function_tool, Runner, ItemHelpers, RunContextWrapper

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

def main():

    token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")

    client = AsyncAzureOpenAI(
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=token_provider,
    )

    # Set the default OpenAI client for the Agents SDK
    set_default_openai_client(client)
    set_default_openai_api ("chat_completions")
    set_tracing_disabled(True)

    agent = Agent(
        name="Explorer Agent",
        instructions="You are an explorer agent which helps in finding information about places.",
        # model = OpenAIChatCompletionsModel(openai_client=client,
        #     model=os.getenv("AZURE_OPENAI_DEPLOYMENT"))
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT")
    )

    response = Runner.run_sync(agent, "I am going to Paris, what should I see?")
    print(response.final_output)

    # Set up console tracing
    # console_exporter = ConsoleSpanExporter()
    # console_processor = BatchTraceProcessor(exporter=console_exporter)
    # add_trace_processor(console_processor)


if __name__ == "__main__":
    main()


