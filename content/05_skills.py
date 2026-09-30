import asyncio
import datetime
import os
from pathlib import Path

import logfire
import pandas as pd
from openai import AsyncOpenAI
from zoneinfo import ZoneInfo

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.capabilities import MCP


logfire.configure(service_name="mcp_client", send_to_logfire=False)
logfire.instrument_pydantic_ai()

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", default="EMPTY"),
    base_url="https://aitta-api.csc.fi/openai/v1",
)

policy_text = (Path(__file__).parent / "skills" / "travel-policy" / "skill.md").read_text()

model = OpenAIChatModel(
    "google/gemma-4-31b-it",
    provider=OpenAIProvider(openai_client=client),
    instructions=f"""
You are a helpful travel assistant. 
You must apply the following skill:

{policy_text}
"""
)
agent = Agent(model,
              capabilities=[MCP(url="http://localhost:8000/mcp")]
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
    # Building on lesson 03: search_flights now takes a concrete date, so a relative
    # date forces the agent to CHAIN the tools -- first get_current_datetime, then
    # feed the resolved date into search_flights.
    #   "Are there any flights from Paris to Rome tomorrow?"   -> get_current_datetime, then search_flights
    #   "I want to fly from Munich to Lisbon this Friday."     -> get_current_datetime, then search_flights
    #   "And the day after? What about the cheapest one?"      -> reuses history to keep the context
    asyncio.run(main())
