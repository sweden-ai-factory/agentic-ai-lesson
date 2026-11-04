import asyncio
import os
from pathlib import Path

import logfire
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.capabilities import MCP, LocalWorkspace
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai_harness import Skills

load_dotenv()

logfire.configure(service_name="skills_agent", send_to_logfire=False)
logfire.instrument_pydantic_ai()

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", default="EMPTY"),
    base_url=os.getenv("MODEL_BASE_URL", "https://aitta-api.csc.fi/openai/v1"),
)


model = OpenAIChatModel(
    os.getenv("MODEL_NAME", "google/gemma-4-31b-it"),
    provider=OpenAIProvider(openai_client=client),
)
agent = Agent(
    model,
    name="travel_agent",
    instructions="You are a helpful travel assistant. Before answering, load any capability or skill relevant to the request.",
    capabilities=[
        MCP(url=f"http://127.0.0.1:{os.getenv('MCP_PORT', '8000')}/mcp"),
        # `Skills` reads SKILL.md files through the run's workspace, so attach one rooted
        # at this script's directory: "./agent-skills" then resolves to hands-on/agent-skills
        # no matter where the lesson is launched from.
        LocalWorkspace(Path(__file__).parent),
        Skills("./agent-skills", include=["travel-policy"]),
    ],
)


async def main():
    history = []
    while True:
        try:
            prompt = input("You: ")
        except (EOFError, KeyboardInterrupt):
            break
        if prompt.strip().lower() in {"quit", "exit", ""}:
            break

        async with agent.run_stream(prompt, message_history=history) as result:
            print("Agent: ", end="")
            async for text in result.stream_text(delta=True):
                print(text, end="", flush=True)
            print()
        history = result.all_messages()


if __name__ == "__main__":
    # Start the MCP server with the book_flight tool first:
    #   uv run 03_mcp_server_solution.py
    #
    # As in 02b_flight_search.py: search_flights takes a concrete date, so a relative
    # date forces the agent to CHAIN the tools -- first get_current_datetime, then
    # feed the resolved date into search_flights.
    #   "Are there any flights from Paris to Rome tomorrow?"   -> get_current_datetime, then search_flights
    #   "Does it comply with the travel policy?"               -> applies the instructions from the skill
    #
    # To invoke the skill, if it does not happen automatically, you can prompt
    #
    #   "/travel-policy"                                       -> You should see running tool: load_capability
    asyncio.run(main())
