import asyncio
import contextlib
import logging
import signal
import sys
import os
import agents
from openai import AsyncAzureOpenAI

from src.prompts import REACT_INSTRUCTIONS
from src.utils.langfuse.shared_client import langfuse_client

from dotenv import load_dotenv
load_dotenv()

from src.utils.azure_openai.client import get_openai_client
from src.utils.tools.mongodb.atlas_mongo_util import MongoManager
from agents import Agent, Runner, ModelSettings, function_tool, OpenAIChatCompletionsModel
from agents import set_default_openai_client,set_default_openai_api,set_tracing_disabled
from pydantic import BaseModel

mongo = MongoManager()
openai_client = get_openai_client()

# Set the default OpenAI client for the Agents SDK at the global level once
set_default_openai_client(openai_client)
set_default_openai_api ("chat_completions")
set_tracing_disabled(True)


class AgentOutput(BaseModel):
    final_output: str
    sourceUrl: list[str]
    
def structured_output(final_output: str, source_url: list[str]) -> AgentOutput:
    """Structure the output from the agent into a AgentOutput model."""
    return AgentOutput(final_output=final_output, sourceUrl=source_url).model.schema_json()


# Strictly follow the output format using the structured_output tool.
# Executor Agent: handles long context efficiently
executor_agent = Agent(
    name="ProductSupportAgent",
    instructions=(
        "You are a product support assistant with access to a knowledge base. Given a search query, you should use the perform_vector_search tool to fetch relevant documents.\
         Do NOT return raw search results."
    ),
    tools=[
        function_tool(mongo.perform_vector_search)
    ],
    # model=OpenAIChatCompletionsModel(
    #     model="gpt-4o-2024-08-06", openai_client=openai_client
    # ),
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    model_settings=ModelSettings(temperature=0),
)

# Main Agent: Orchestrator
main_agent = Agent(
    name="MainAgent",
    instructions=REACT_INSTRUCTIONS,
    # Allow the planner agent to invoke the worker agent.
    # The long context provided to the worker agent is hidden from the main agent.
    tools=[
        executor_agent.as_tool(
            tool_name="search_tool",
            tool_description="Perform search for a query and return a concise summary.",
        ), function_tool(structured_output)

    ],
    # model=OpenAIChatCompletionsModel(
    #     model="gpt-4o-2024-08-06", openai_client=openai_client
    # ),
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    model_settings=ModelSettings(temperature=0),
)

question = "Can you recommend a paderno kettle that has a capacity more than 1.5L?"

async def main():

    # run planner agent
    result_main = await Runner.run(
        main_agent,
        input=question,
    )

    print("--- Planning ---")
    print()
    print("--- Planner Agent Output ---")
    print(f"Planner Response: {result_main.final_output}")
    print()


    # print("--- Executing ---")
    # result_worker = await Runner.run(
    #         executor_agent,
    #         input=result_main
    # )
    # print()
    # print("--- Executor Agent Output ---")
    # print(f"Worker Response: {result_worker.final_output}")
    # print()
    

if __name__ == "__main__":
    asyncio.run(main())