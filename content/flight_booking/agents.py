"""Agent definitions for the flight booking application."""

import datetime
from dataclasses import dataclass
from typing import Literal

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext

from .config import model

# Data models for the agents.

@dataclass
class Deps:
    web_page_text: str
    date: datetime.date

class TripRequest(BaseModel):
    """Details of the trip request by the user."""
    req_origin: str
    req_destination: str


class FlightDetails(BaseModel):
    """Details of the most suitable flight."""

    flight_number: str
    price: int
    origin: str = Field(description='Three-letter airport code')
    destination: str = Field(description='Three-letter airport code')
    date: datetime.date


class NoFlightFound(BaseModel):
    """When no valid flight is found."""


class SeatPreference(BaseModel):
    row: int = Field(ge=1, le=30)
    seat: Literal['A', 'B', 'C', 'D', 'E', 'F']


class Failed(BaseModel):
    """Unable to extract a seat selection."""

# This agent is responsible for extracting flight details from web page text.
extraction_agent = Agent(
    model,
    output_type=list[FlightDetails],
    instructions='Extract all the flight details from the given text.',
)


# This agent is responsible for controlling the flow of the conversation.
search_agent = Agent[Deps, FlightDetails | NoFlightFound](
    model,
    output_type=FlightDetails | NoFlightFound,
    deps_type=Deps,
    retries=4,
    instructions=(
        'Your job is to find the cheapest flight for the user on the given date. '
    ),
)


@search_agent.tool
async def extract_flights(ctx: RunContext[Deps]) -> list[FlightDetails]:
    """Get details of all flights."""
    # we pass the usage to the search agent so requests within this agent are counted
    result = await extraction_agent.run(ctx.deps.web_page_text, usage=ctx.usage)
    logfire.info('found {flight_count} flights', flight_count=len(result.output))
    return result.output


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
    if output.date != ctx.deps.req_date:
        errors.append(f'Flight should be on {ctx.deps.req_date}, not {output.date}')

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
