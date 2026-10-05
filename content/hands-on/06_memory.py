import asyncio
import os
from pathlib import Path

import logfire
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.capabilities import MCP, LocalWorkspace
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai_harness import Memory, Skills
from pydantic_ai_harness.memory import FileStore

load_dotenv()

logfire.configure(service_name="mcp_client", send_to_logfire=False)
logfire.instrument_pydantic_ai()

# A distilled, long-term memory lives as Markdown files under this directory.
# resolves it inside the run's workspace (the `LocalWorkspace` below, rooted at
# this script's directory), so the main notebook lands in
# content/agent-memory/main/MEMORY.md ("main" is the agent's storage segment) and
# survives across sessions.
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
        MCP(url="http://127.0.0.1:8000/mcp"),
        # `Skills` reads SKILL.md files through the run's workspace, so attach one rooted
        # at this script's directory: "skills" then resolves to content/skills no matter
        # where the lesson is launched from.
        LocalWorkspace(Path(__file__).parent),
        Skills("./agent-skills", include=["travel-policy"]),
        # Cross-session memory, replacing lesson 05's --remember-history flag: instead
        # of dumping the raw conversation history to travel_history.json, the agent now
        # keeps its own Markdown notebook under MEMORY_DIR. `Memory` gives it the
        # write_memory, read_memory, delete_memory, and search_memory tools, and
        # injects a bounded excerpt of MEMORY.md into every request. Tell it something
        # durable ("I prefer morning flights") and it calls write_memory; on the next
        # run the notebook is injected back into the prompt, so it no longer asks for
        # your preferences.
        Memory(FileStore(MEMORY_DIR)),
    ],
)


async def main():
    # Cross-session memory is no longer our job here --
    # the Memory capability persists facts to MEMORY_DIR as the agent writes them.
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


if __name__ == "__main__":
    # Building on lesson 05: skill to replace the history functionality with a "Memory system"
    #
    # Try starting with
    #
    #   "Hi"
    #
    # To interact with the memory you can prompt
    #
    #   "Remember that my name is Joan"  -> We already did that for you
    #   "Remember that I live in Stockholm"
    #
    # Memory
    #   python 06_memory.py     -> tell the agent something durable ("I prefer morning
    #                              flights") and watch it call write_memory; quit and
    #                              restart, and the notebook in
    #                              content/agent-memory/main/MEMORY.md is injected
    #                              back into the prompt, so it does NOT ask for your
    #                              preferences again. No flag needed: long-term memory
    #                              is always on now.
    asyncio.run(main())
