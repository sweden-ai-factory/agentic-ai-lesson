import asyncio
import datetime
import os
from pathlib import Path

import logfire
import pandas as pd
from dotenv import load_dotenv
from openai import AsyncOpenAI
from zoneinfo import ZoneInfo

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()

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

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


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


@agent.tool_plain
def search_flights(
    origin: str | None = None,
    destination: str | None = None,
    date: str | None = None,
) -> str:
    """Search the weekly flight schedule. Flights recur on fixed weekdays.

    Args:
        origin: departure city, e.g. 'Helsinki'. Omit to match any.
        destination: arrival city, e.g. 'Stockholm'. Omit to match any.
        date: travel date 'YYYY-MM-DD'; returns flights on that weekday. Resolve
            relative dates like 'tomorrow' with get_current_datetime first.
    """
    logfire.info("tool called with {origin=} {destination=} {date=}", origin=origin, destination=destination, date=date)
    flights = pd.read_csv(Path(__file__).parent / "data" / "flights.csv")
    if origin:
        flights = flights[flights["origin"].str.lower() == origin.lower()]
    if destination:
        flights = flights[flights["destination"].str.lower() == destination.lower()]
    if date:
        try:
            weekday = WEEKDAYS[datetime.date.fromisoformat(date).weekday()]
        except ValueError:
            return f"Invalid date {date!r}, expected 'YYYY-MM-DD'."
        flights = flights[flights["weekdays"].str.contains(weekday)]

    if flights.empty:
        result = "No matching flights found."
    else:
        result = flights.head(20).to_string(index=False)
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
        history = result.all_messages()


if __name__ == "__main__":
    # Building on lesson 03: search_flights now takes a concrete date, so a relative
    # date forces the agent to CHAIN the tools -- first get_current_datetime, then
    # feed the resolved date into search_flights.
    #   "Are there any flights from Paris to Rome tomorrow?"   -> get_current_datetime, then search_flights
    #   "I want to fly from Munich to Lisbon this Friday."     -> get_current_datetime, then search_flights
    #   "And the day after? What about the cheapest one?"      -> reuses history to keep the context
    asyncio.run(main())
