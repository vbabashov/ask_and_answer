import asyncio
import contextlib
import logging
import signal
import sys
import os
import agents
from openai import AsyncAzureOpenAI

from prompts import REACT_INSTRUCTIONS
from utils.langfuse.shared_client import langfuse_client

from dotenv import load_dotenv
load_dotenv()

from utils.azure_openai.client import get_openai_client
from utils.tools.mongodb.atlas_mongo_util import MongoManager
from utils.functions import handle_stream_events
from agents import Agent, Runner, ModelSettings, function_tool
from agents import set_default_openai_client,set_default_openai_api,set_tracing_disabled
from pydantic import BaseModel


mongo = MongoManager()
openai_client = get_openai_client()

# Set the default OpenAI client for the Agents SDK at the global level once
set_default_openai_client(openai_client)
set_default_openai_api ("chat_completions")
set_tracing_disabled(True)


# Executor Agent: handles long context efficiently
executor_agent = Agent(
    name="SearchAgent",
    instructions=(
        "You are a product support agent. You receive a single search query as input. "
        "Use the KnowledgeBaseTool to perform a search, then produce a concise "
        "'search summary' of the key findings. Do NOT return raw search results."
    ),
    tools=[
        function_tool(mongo.perform_vector_search),
    ],
    # model=OpenAIChatCompletionsModel(
    #     model="gpt-4o", openai_client=openai_client
    # ),
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT")
)

# Main Agent:
main_agent = Agent(
    name="MainAgent",
    instructions=REACT_INSTRUCTIONS,
    # Allow the planner agent to invoke the worker agent.
    # The long context provided to the worker agent is hidden from the main agent.
    tools=[
        executor_agent.as_tool(
            tool_name="search",
            tool_description="Perform search for a query and return a concise summary.",
        )
    ],

    # a larger, more capable model for planning and reasoning over summaries
    # model=OpenAIChatCompletionsModel(
    #     model="gpt-4o", openai_client=openai_client
    # ),
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT")
)

question = "What is the manufacturing warranty period for the espresso machines"

async def main():

    # run planner agent
    result = Runner.run_streamed(
        main_agent, 
        input = question,
    )

    # handle stream events
    print("--- Analyzing ---")
    await handle_stream_events(result)

    # print planner agent's output
    print()
    print("--- Planner Agent Output ---")
    print(result.final_output)
    print()

    # # check if execution is required
    # if result.final_output.exec_required:
    #     print("Final Output Exec Inst:", result.final_output)  # Debug log
    #     result = Runner.run_streamed(
    #         executor_agent,
    #         result.final_output
    #     )
    
    #     print("--- Executing ---")
    #     await handle_stream_events(result)

    #     print()
    #     print("--- Executor Agent Output ---")
    #     print(result.final_output)
    #     print()



if __name__ == "__main__":
    asyncio.run(main())