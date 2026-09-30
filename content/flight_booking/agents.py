"""Agent definitions for the flight booking application."""

import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

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
    date: datetime.date
    req_origin: str = ''
    req_destination: str = ''

class TripRequest(BaseModel):
    """Details of the trip request by the user."""
    req_origin: str
    req_destination: str


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
search_agent = Agent[Deps, FlightDetails | NoFlightFound](
    model,
    output_type=FlightDetails | NoFlightFound,
    deps_type=Deps,
    retries=4,
    instructions=(
        'Your job is to find the cheapest flight for the user on the given date. '
        'Use the search_flights tool to look up matching flights, then return the '
        'cheapest one. The flight date is the requested travel date.'
    ),
)


@search_agent.tool
async def search_flights(ctx: RunContext[Deps]) -> str:
    """Search the weekly flight schedule for flights matching the requested trip.

    Flights recur on fixed weekdays; a flight matches if it operates on the
    weekday of the requested date.
    """
    flights = pd.read_csv(FLIGHTS_CSV)
    if ctx.deps.req_origin:
        flights = flights[flights['origin'].str.lower() == ctx.deps.req_origin.lower()]
    if ctx.deps.req_destination:
        flights = flights[
            flights['destination'].str.lower() == ctx.deps.req_destination.lower()
        ]
    weekday = WEEKDAYS[ctx.deps.date.weekday()]
    flights = flights[flights['weekdays'].str.contains(weekday)]

    logfire.info('found {flight_count} flights', flight_count=len(flights))
    if flights.empty:
        return 'No matching flights found.'
    return flights.head(20).to_string(index=False)


@search_agent.output_validator
async def validate_output(
    ctx: RunContext[Deps], output: FlightDetails | NoFlightFound
) -> FlightDetails | NoFlightFound:
    """Procedural validation that the flight meets the constraints."""
    if isinstance(output, NoFlightFound):
        return output

    errors: list[str] = []
    if output.origin != ctx.deps.req_origin:
        errors.append(
            f'Flight should have origin {ctx.deps.req_origin}, not {output.origin}'
        )
    if output.destination != ctx.deps.req_destination:
        errors.append(
            f'Flight should have destination {ctx.deps.req_destination}, not {output.destination}'
        )
    if output.date != ctx.deps.date:
        errors.append(f'Flight should be on {ctx.deps.date}, not {output.date}')

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

# This agent is responsible for extracting trip request from user
# TODO: add date into request and in search agent
conversational_agent = Agent[TripRequest](
    model,
    deps_type=Deps,
    output_type=TripRequest,
    instructions=(
        "You are a helpful assistant that helps the user find a flight. "
        "Extract the origin and desination of the trip the user is looking for."
    ),
)
