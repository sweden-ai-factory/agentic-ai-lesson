"""Agent definitions for the flight booking application."""

import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

import logfire
import pandas as pd
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext

from .config import model

# The shared weekly flight schedule used across the lessons (see 03_flight_search.py).
FLIGHTS_CSV = Path(__file__).parent.parent / 'data' / 'flights.csv'
WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

# Data models for the agents.

@dataclass
class Deps:
    req_origin: str = ''
    req_destination: str = ''

class TripRequest(BaseModel):
    """Details of the trip request by the user."""
    req_origin: str
    req_destination: str
    req_date: str = Field(
        description=(
            'Travel date exactly as the user phrased it, e.g. "tomorrow", '
            '"next Friday", or "2025-01-15". Use "today" if unspecified.'
        )
    )


class FlightDetails(BaseModel):
    """Details of the most suitable flight."""

    flight_number: str
    price: int
    origin: str = Field(description='Departure city')
    destination: str = Field(description='Arrival city')
    date: datetime.date


class NoFlightFound(BaseModel):
    """When no valid flight is found."""


class SeatPreference(BaseModel):
    row: int = Field(ge=1, le=30)
    seat: Literal['A', 'B', 'C', 'D', 'E', 'F']


class Failed(BaseModel):
    """Unable to extract a seat selection."""

# This agent is responsible for controlling the flow of the conversation.
search_agent = Agent[Deps, list[FlightDetails] | NoFlightFound](
    model,
    output_type=list[FlightDetails] | NoFlightFound,
    deps_type=Deps,
    retries=4,
    instructions=(
        'Your job is to find flights for the user on the requested date. '
        'First resolve the travel date to a concrete YYYY-MM-DD date, using the '
        'get_current_datetime tool for relative dates like "tomorrow" or "next Friday". '
        'Then use search_flights to look up matching flights and return all of them '
        'sorted by price (cheapest first), each with its date set to the resolved '
        'travel date. Return NoFlightFound only if there are no matching flights.'
    ),
)


@search_agent.tool_plain
def get_current_datetime(timezone: str | None = None) -> str:
    """Get the current date and time.

    Args:
        timezone: IANA timezone name, e.g. 'Europe/Stockholm'. Omit for the user's local time.
    """
    logfire.info('tool called with {timezone=}', timezone=timezone)
    tz = ZoneInfo(timezone) if timezone else None
    now = datetime.datetime.now(tz).astimezone(tz)
    result = now.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')
    logfire.info('tool result: {result}', result=result)
    return result


@search_agent.tool_plain
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search the weekly flight schedule. Flights recur on fixed weekdays.

    Args:
        origin: departure city, e.g. 'Amsterdam'.
        destination: arrival city, e.g. 'Barcelona'.
        date: travel date 'YYYY-MM-DD'; returns flights on that weekday. Resolve
            relative dates like 'tomorrow' with get_current_datetime first.
    """
    logfire.info(
        'tool called with {origin=} {destination=} {date=}',
        origin=origin,
        destination=destination,
        date=date,
    )
    flights = pd.read_csv(FLIGHTS_CSV)
    if origin:
        flights = flights[flights['origin'].str.lower() == origin.lower()]
    if destination:
        flights = flights[flights['destination'].str.lower() == destination.lower()]
    try:
        weekday = WEEKDAYS[datetime.date.fromisoformat(date).weekday()]
    except ValueError:
        return f"Invalid date {date!r}, expected 'YYYY-MM-DD'."
    flights = flights[flights['weekdays'].str.contains(weekday)]

    logfire.info('found {flight_count} flights', flight_count=len(flights))
    if flights.empty:
        return 'No matching flights found.'
    return flights.head(20).to_string(index=False)


@search_agent.output_validator
async def validate_output(
    ctx: RunContext[Deps], output: list[FlightDetails] | NoFlightFound
) -> list[FlightDetails] | NoFlightFound:
    """Procedural validation that every returned flight meets the constraints."""
    if isinstance(output, NoFlightFound):
        return output

    errors: list[str] = []
    for flight in output:
        if flight.origin.lower() != ctx.deps.req_origin.lower():
            errors.append(
                f'Flight {flight.flight_number} should have origin '
                f'{ctx.deps.req_origin}, not {flight.origin}'
            )
        if flight.destination.lower() != ctx.deps.req_destination.lower():
            errors.append(
                f'Flight {flight.flight_number} should have destination '
                f'{ctx.deps.req_destination}, not {flight.destination}'
            )

    if errors:
        raise ModelRetry('\n'.join(errors))
    else:
        return output


# This agent is responsible for extracting the user's seat selection
seat_preference_agent = Agent[object, SeatPreference | Failed](
    model,
    output_type=SeatPreference | Failed,
    instructions=(
        "Extract the user's seat preference. "
        'Seats A and F are window seats. '
        'Row 1 is the front row and has extra leg room. '
        'Rows 14, and 20 also have extra leg room. '
    ),
)

# This agent is responsible for extracting the trip request from the user.
conversational_agent = Agent[TripRequest](
    model,
    deps_type=Deps,
    output_type=TripRequest,
    instructions=(
        "You are a helpful assistant that helps the user find a flight. "
        "Extract the origin, destination, and travel date of the trip the user "
        "is looking for. Keep the date exactly as the user phrased it (e.g. "
        "'tomorrow' or 'next Friday') and do not resolve it yourself; use 'today' "
        "if the user did not specify a date."
    ),
)
