"""Agent definitions for the flight booking application."""

import datetime
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.capabilities import MCP

from .config import model

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


class NoFlightFound(BaseModel):
    """When no valid flight is found."""


class SeatPreference(BaseModel):
    row: int = Field(ge=1, le=30)
    seat: Literal['A', 'B', 'C', 'D', 'E', 'F']


class Failed(BaseModel):
    """Unable to extract a seat selection."""

# Its tools (get_current_datetime and search_flights) come from the lesson 04
# MCP server (04_mcp_server.py), which must be running at the URL below.
search_agent = Agent[Deps, list[FlightDetails] | NoFlightFound](
    model,
    output_type=list[FlightDetails] | NoFlightFound,
    deps_type=Deps,
    retries=4,
    capabilities=[MCP(url='http://127.0.0.1:8000/mcp')],
    instructions=(
        'Your job is to find flights for the user on the requested date. '
        'First resolve the travel date to a concrete YYYY-MM-DD date, using the '
        'get_current_datetime tool for relative dates like "tomorrow" or "next Friday". '
        'Then use search_flights to look up matching flights and return all of them '
        'sorted by price (cheapest first), each with its date set to the resolved '
        'travel date. Add the arrival and departure time as well. Return NoFlightFound only if there are no matching flights.'
    ),
)


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
        'Seats B and E are middle seats and C and D are aisle seats'
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
