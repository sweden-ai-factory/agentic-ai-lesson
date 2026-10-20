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
        MCP(url="http://127.0.0.1:8000/mcp"),
        # Resolve paths relative to this script's directory
        LocalWorkspace(Path(__file__).parent),
        Skills("./agent-skills", include=["travel-policy"]),
        # The agent writes notes to MEMORY.md, which is injected into every request
        Memory(FileStore(MEMORY_DIR)),
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
    # Prompts to try:
    #   "Hi"
    #   "Remember that I live in Stockholm"
    #
    # To reset the memory: git checkout -- agent-memory/main/MEMORY.md
    asyncio.run(main())
