import asyncio
import argparse
import datetime
import os

import logfire
from dotenv import load_dotenv
from openai import AsyncOpenAI
from zoneinfo import ZoneInfo

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--enable_tools", action="store_true")
parser.add_argument("--enable_history", action="store_true")
args = parser.parse_args()

logfire.configure(send_to_logfire=False)
logfire.instrument_pydantic_ai()

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", default="EMPTY"),
    base_url="https://aitta-api.csc.fi/openai/v1",
)

model = OpenAIChatModel(
    "google/gemma-4-31b-it",
    provider=OpenAIProvider(openai_client=client),
)
agent = Agent(model)

if args.enable_tools:
    @agent.tool_plain
    def get_current_datetime(timezone: str | None = None) -> str:
        """Get the current date and time.

        Args:
            timezone: IANA timezone name, e.g. 'Europe/Stockholm'. Omit for the user's local time.
        """
        logfire.info("tool called with {timezone=}", timezone=timezone)
        tz = ZoneInfo(timezone) if timezone else None
        now = datetime.datetime.now(tz).astimezone(tz)
        result = now.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
        logfire.info("tool result: {result}", result=result)
        return result

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
        history = result.all_messages() if args.enable_history else []


if __name__ == "__main__":
    # python3 content/02_time.py -> hallucinates 
    # python3 content/02_time.py --enable_tools -> knows how to check time, but doesn't memorize prompt before
    # python3 content/02_time.py --enable_tools --enable_history -> works quite well
    asyncio.run(main())
