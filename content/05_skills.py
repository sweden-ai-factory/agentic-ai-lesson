import argparse
import asyncio
import os
from pathlib import Path

import logfire
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import TypeAdapter
from pydantic_ai import Agent
from pydantic_ai.capabilities import MCP, LocalWorkspace
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai_harness import Skills

load_dotenv()

logfire.configure(service_name="mcp_client", send_to_logfire=False)
logfire.instrument_pydantic_ai()

HISTORY_FILE = Path(__file__).parent / "travel_history.json"

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", default="EMPTY"),
    base_url="https://aitta-api.csc.fi/openai/v1",
)


model = OpenAIChatModel(
    "google/gemma-4-31b-it",
    provider=OpenAIProvider(openai_client=client),
)
agent = Agent(
    model,
    name="travel_agent",
    instructions="You are a helpful travel assistant. Before answering, load any capability or skill relevant to the request.",
    capabilities=[
        MCP(url="http://127.0.0.1:8000/mcp"),
        # `Skills` reads SKILL.md files through the run's workspace, so attach one rooted
        # at this script's directory: "skills" then resolves to content/skills no matter
        # where the lesson is launched from.
        LocalWorkspace(Path(__file__).parent),
        Skills("./skills", include=["travel-policy"]),
    ],
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Travel assistant with optional cross-session memory."
    )
    parser.add_argument(
        "--remember-history",
        action="store_true",
        help="Persist the conversation history to disk, so facts learned in a "
        "previous session (e.g. morning vs. afternoon flight preference) "
        "are remembered when you start a new session.",
    )
    return parser.parse_args()


def load_history() -> list[ModelMessage]:
    """Load a previously saved conversation history, if any."""
    if not HISTORY_FILE.exists():
        return []
    try:
        history = TypeAdapter(list[ModelMessage]).validate_json(
            HISTORY_FILE.read_text()
        )
    except Exception as exc:  # corrupted file -> start fresh instead of crashing
        print(
            f"Warning: could not load {HISTORY_FILE} ({exc}); starting with an empty history."
        )
        return []
    print(f"(Remembered {len(history)} messages from previous session: {HISTORY_FILE})")
    return history


def save_history(history: list[ModelMessage]) -> None:
    """Persist the conversation history so the next session can resume it."""
    HISTORY_FILE.write_text(TypeAdapter(list[ModelMessage]).dump_json(history).decode())
    print(f"(History saved to {HISTORY_FILE}; it will be remembered next time)")


async def main():
    args = parse_args()
    history = load_history() if args.remember_history else []
    try:
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
    finally:
        if args.remember_history and history:
            save_history(history)


if __name__ == "__main__":
    # Building on lesson 03: search_flights now takes a concrete date, so a relative
    # date forces the agent to CHAIN the tools -- first get_current_datetime, then
    # feed the resolved date into search_flights.
    #   "Are there any flights from Paris to Rome tomorrow?"   -> get_current_datetime, then search_flights
    #   "I want to fly from Munich to Lisbon this Friday."     -> get_current_datetime, then search_flights
    #   "And the day after? What about the cheapest one?"      -> reuses history to keep the context
    #
    # To invoke the skill, if it does not happen automatically, you can prompt
    #
    #   "/travel-policy"                                       -> You should see running tool: load_capability
    #   "Does it comply with the travel policy?"               -> Applies the instructions from the skill
    #
    # Memory (lesson 05 extension):
    #   python 05_skills.py                       -> fresh session every time, the agent asks for your preferences again
    #   python 05_skills.py --remember-history    -> history is saved to travel_history.json on exit and
    #                                                 reloaded on the next run, so learned facts (e.g. whether you
    #                                                 prefer morning or afternoon flights) are NOT asked again.
    asyncio.run(main())
