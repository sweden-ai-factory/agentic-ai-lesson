"""Agent definitions for the flight booking application."""

import datetime
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Literal

import logfire
import pandas as pd
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.capabilities import MCP, LocalWorkspace
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai_harness import Memory, Skills
from pydantic_ai_harness.memory import FileStore

from .config import MCP_URL, model

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
    departure_time: datetime.time
    arrival_time: datetime.time


class FlightSearchResult(BaseModel):
    """All flights returned by the search tool; an empty list means no matches."""

    flights: list[FlightDetails]


class SeatPreference(BaseModel):
    row: int = Field(ge=1, le=30)
    seat: Literal['A', 'B', 'C', 'D', 'E', 'F']


class Failed(BaseModel):
    """Unable to extract a seat selection."""


# This agent is responsible for extracting trip request from user
trip_extractor_agent = Agent[TripRequest](
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
    retries=3,
)

@trip_extractor_agent.output_validator
async def log_trip_request(ctx: RunContext[Deps], output: TripRequest) -> TripRequest:
    """A 'fake' validator meant to intercept and log the trip request."""
    logfire.info(
        'Requested trip from {origin} to {destination} on {date}',
        origin=output.req_origin,
        destination=output.req_destination,
        date=output.req_date
    )
    return output


# The search agent finds flights for the requested trip.
# Its tools (get_current_datetime and search_flights) come from the lesson 04
# MCP server (03_mcp_server.py), which must be running at MCP_URL (see config.py).
search_agent = Agent[Deps, FlightSearchResult](
    model,
    output_type=FlightSearchResult,
    deps_type=Deps,
    retries=4,
    capabilities=[MCP(url=MCP_URL, allowed_tools=["get_current_datetime", "search_flights"])],
    instructions=(
        'Your job is to find flights for the user on the requested date. '
        'First resolve the travel date to a concrete YYYY-MM-DD date, using the '
        'get_current_datetime tool for relative dates like "tomorrow" or "next Friday". '
        'Then call search_flights exactly once, always passing origin, destination, '
        'and the resolved date. Return every row from its result in the flights list, '
        'sorted by price, with flight_no mapped to flight_number, price_eur mapped to '
        'price, and date set to the resolved travel date. Do not add or omit flights, '
        'and do not search again after receiving the result. An empty flights list '
        'means that no matching flights were found.'
    ),
)


def _latest_route_search(ctx: RunContext[Deps]) -> tuple[dict[str, object], str] | None:
    """Find the latest successful search whose route matches the requested trip."""
    calls = {
        part.tool_call_id: part
        for message in ctx.messages
        for part in message.parts
        if isinstance(part, ToolCallPart) and part.tool_name == 'search_flights'
    }
    for message in reversed(ctx.messages):
        for part in reversed(message.parts):
            if not (
                isinstance(part, ToolReturnPart)
                and part.tool_name == 'search_flights'
                and part.outcome == 'success'
                and isinstance(part.content, str)
            ):
                continue
            call = calls.get(part.tool_call_id)
            if call is None:
                continue
            args = call.args_as_dict()
            origin = args.get('origin')
            destination = args.get('destination')
            if (
                isinstance(origin, str)
                and origin.lower() == ctx.deps.req_origin.lower()
                and isinstance(destination, str)
                and destination.lower() == ctx.deps.req_destination.lower()
            ):
                return args, part.content
    return None


def _parse_search_result(args: dict[str, object], content: str) -> FlightSearchResult:
    """Convert the MCP server's fixed-width table into the agent output model."""
    raw_date = args.get('date')
    if not isinstance(raw_date, str):
        raise ModelRetry('Call search_flights with a concrete YYYY-MM-DD date.')
    try:
        travel_date = datetime.date.fromisoformat(raw_date)
    except ValueError as error:
        raise ModelRetry('Call search_flights with a concrete YYYY-MM-DD date.') from error

    if content == 'No matching flights found.':
        return FlightSearchResult(flights=[])

    try:
        table = pd.read_fwf(StringIO(content))
    except ValueError as error:
        raise ModelRetry('The flight search result could not be parsed; try searching again.') from error
    required_columns = {
        'flight_no', 'origin', 'destination', 'departure_time', 'arrival_time', 'price_eur'
    }
    if not required_columns.issubset(table.columns):
        raise ModelRetry('The flight search result could not be parsed; try searching again.')

    flights = [
        FlightDetails(
            flight_number=row.flight_no,
            price=int(row.price_eur),
            origin=row.origin,
            destination=row.destination,
            date=travel_date,
            departure_time=row.departure_time,
            arrival_time=row.arrival_time,
        )
        for row in table.itertuples()
    ]
    flights.sort(key=lambda flight: flight.price)
    return FlightSearchResult(flights=flights)


@search_agent.output_validator
async def validate_flights(
    ctx: RunContext[Deps], output: FlightSearchResult
) -> FlightSearchResult:
    """Require a real search and use its result as the source of truth."""
    search = _latest_route_search(ctx)
    if search is None:
        raise ModelRetry(
            f'Call search_flights with origin {ctx.deps.req_origin}, '
            f'destination {ctx.deps.req_destination}, and a concrete date before returning.'
        )

    # The model still produces the structured output, but it cannot invent or omit
    # flights while formatting it: the tool response contains the canonical result.
    tool_output = _parse_search_result(*search)
    if output != tool_output:
        logfire.info('Replacing flight output that differs from the search tool result')

    errors: list[str] = []
    for flight in tool_output.flights:
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
    return tool_output


# This agent is responsible for extracting the user's seat selection
seat_preference_agent = Agent[object, SeatPreference | Failed](
    model,
    output_type=SeatPreference | Failed,
    instructions=(
        "Extract the user's seat preference. "
        'Seats A and F are window seats. '
        'Seats B and E are middle seats and C and D are aisle seats'
        'Row 1 is the front row and has extra leg room. '
        'Rows 14, and 20 also have extra leg room. '
    ),
)

# The book agent books the selected flight.
# Memory files are stored in hands-on/agent-memory/main/
MEMORY_DIR = "agent-memory"

book_agent = Agent[tuple[FlightDetails, SeatPreference], str](
    model,
    deps_type=tuple[FlightDetails, SeatPreference],
    output_type=str,
    capabilities=[
        MCP(url=MCP_URL), #, allowed_tools=["book_flight"]),
        # Resolve paths relative to the "hands-on" directory
        LocalWorkspace(Path(__file__).parent.parent),
        Skills("./agent-skills", include=["travel-policy"]),
        # The agent writes notes to MEMORY.md, which is injected into every request
        Memory(FileStore(MEMORY_DIR)),
    ],
    instructions=(
        'You are a flight booking agent. '
        'Do not request the user for further input and use deps and memory to fill in missing information. '
        'Before booking ensure with the skill that it complies with travel policy. '
        'If all checks pass, book the flight for the user and return the booking confirmation in plain text. '
    )
)
