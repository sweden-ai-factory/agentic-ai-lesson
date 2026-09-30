import datetime
from pathlib import Path

import logfire
import pandas as pd
from zoneinfo import ZoneInfo

from mcp.server import MCPServer

mcp = logfire.configure(service_name="mcp-server", send_to_logfire=False)
logfire.instrument_pydantic_ai()

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

mcp = MCPServer("Demo")


@mcp.tool()
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


@mcp.tool()
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
