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
from pydantic_ai_harness import Memory, Skills
from pydantic_ai_harness.memory import FileStore
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import ArgumentCorrectness, MaxToolCalls, TrajectoryMatch

load_dotenv()

logfire.configure(service_name="mcp_client", send_to_logfire=False)
logfire.instrument_pydantic_ai()

# Memory files are stored in hands-on/agent-memory/main/
MEMORY_DIR = "agent-memory"

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
    instructions=(
        "You are a helpful travel assistant. "
        "Before answering, load any capability or skill relevant to the request. "
        "Use tools named *_memory to understand and to give personalized recommendations."
    ),
    capabilities=[
        MCP(url=f"http://127.0.0.1:{os.getenv('MCP_PORT', '8000')}/mcp"),
        # Resolve paths relative to this script's directory
        LocalWorkspace(Path(__file__).parent),
        Skills("./agent-skills", include=["travel-policy"]),
        # The agent writes notes to MEMORY.md, which is injected into every request
        Memory(FileStore(MEMORY_DIR)),
    ],
)

async def run_agent_eval(prompt: str):
    result = await agent.run(prompt)
    return result


cases = [
    Case(
        name="flight_search",
        inputs="Are there any flights from Paris to Rome tomorrow?",
        evaluators=[
            TrajectoryMatch(
                expected_trajectory=[
                    "get_current_datetime",
                    "search_flights",
                ]
            ),
            ArgumentCorrectness(
                tool_name="search_flights",
                expected_arguments={
                    "origin": "Paris",
                    "destination": "Rome",
                },
            ),
            MaxToolCalls(max_calls=2),
        ],
    ),
    Case(
        name="flight_search_broken",
        inputs="Today is 2026-10-28. Are there any transportations from Paris to Rome tomorrow?",
        evaluators=[
            TrajectoryMatch(
                expected_trajectory=[
                    "get_current_datetime",
                    "search_flights",
                ]
            ),
            ArgumentCorrectness(
                tool_name="search_flights",
                expected_arguments={
                    "origin": "Paris",
                    "destination": "Rome",
                },
            ),
            MaxToolCalls(max_calls=2),
        ],
    ),
]

async def main():
    report = await Dataset(name="experiment", cases=cases).evaluate(run_agent_eval)
    print("\n=====Evaluation report=====")
    print(report)


if __name__ == "__main__":
    # Prompts to try:
    #   "Hi"
    #   "Remember that I live in Stockholm"
    #
    # To reset the memory: git checkout -- agent-memory/main/MEMORY.md
    asyncio.run(main())
