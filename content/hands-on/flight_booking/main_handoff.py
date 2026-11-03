"""Main application flow for the flight booking system.

This is the "programmatic agent hand-off" pattern: a plain async function
calls each specialist agent in turn -- trip extractor, flight search, seat
preference, booking -- and decides in code what happens next. Compare with
main_delegation.py, where an orchestrator agent makes those decisions itself.
"""
import logfire
from pydantic_ai import ModelMessage, ModelResponse, ModelRetry, RunContext, RunUsage  # noqa: F401
from rich.prompt import Prompt

from .agents import (
    FlightDetails,
    NoFlightFound,
    SeatPreference,
    TripRequest,
    book_agent,
    search_agent,
    seat_preference_agent,
    trip_extractor_agent,
)
from .config import usage_limits

QUIT_WORDS = {'quit', 'exit'}

type MessageHistory = list[ModelMessage | ModelResponse]


async def infer_trip_request_via_trip_extractor_agent(
    user_prompt: str,
    message_history: list[ModelMessage] | None,
    usage: RunUsage,
) -> tuple[TripRequest, MessageHistory]:
    """Turn the user's prompt into a TripRequest.

    The message history is kept so follow-ups like "make it next Monday" or
    "try Rome instead" refine the previous request rather than starting over.
    """
    with logfire.span('Trip Extractor Agent: str -> TripRequest'):
        result = await trip_extractor_agent.run(
            user_prompt,
            message_history=message_history,
            usage=usage,
            usage_limits=usage_limits,
        )
        trip = result.output
        return trip, result.all_messages()


async def infer_flights_via_search_agent(
    trip: TripRequest, usage: RunUsage
) -> list[FlightDetails] | NoFlightFound:
    """Find flights for the trip, or None when there are none."""
    with logfire.span('Search Agent: TripRequest -> Flights'):
        result = await search_agent.run(
            f'Find me a flight from {trip.req_origin} to {trip.req_destination} on {trip.req_date}',
            deps=trip,
            usage=usage,
            usage_limits=usage_limits,
        )
        return result.output


def display_flights(flights: list[FlightDetails]) -> None:
    print(f'Found {len(flights)} flight(s):')
    for i, flight in enumerate(flights, start=1):
        print(
            f'  {i}. {flight.flight_number}: {flight.origin} -> '
            f'{flight.destination} on {flight.date}: '
            f'{flight.departure_time} - {flight.arrival_time} for €{flight.price}'
        )


def select_flight(flights: list[FlightDetails]) -> FlightDetails | None:
    """Let the user pick a flight, or None to change the trip instead."""
    answer = Prompt.ask(
        '🤖 Enter the number of the flight to buy, or press Enter to change your trip\nYou',
        choices=[str(i) for i in range(1, len(flights) + 1)] + [''],
        show_choices=False,
    )
    return flights[int(answer) - 1] if answer else None


async def infer_seat_via_seat_preference_agent(usage: RunUsage) -> SeatPreference:
    """Ask the user for a seat until the agent returns a valid one."""
    short_term_history: list[ModelMessage] | None = None
    while True:
        answer = input('🤖 What seat would you like?\nYou: ')

        with logfire.span('Seat Preference Agent: str -> SeatPreference'):
            result = await seat_preference_agent.run(
                answer,
                message_history=short_term_history,
                usage=usage,
                usage_limits=usage_limits,
            )
            if isinstance(result.output, SeatPreference):
                return result.output

            print('Could not understand seat preference. Please try again.')
            short_term_history = result.all_messages()


async def infer_purchase_via_book_agent(
    usage: RunUsage, flight_details: FlightDetails, seat: SeatPreference
) -> list[ModelMessage]:
    """Purchase the flight and record the seat through the booking agent."""
    print(f'Purchasing flight {flight_details=!r} {seat=!r}...')
    with logfire.span('Book Agent: purchase a flight'):
        result = await book_agent.run(
            f'Book the flight {flight_details=} and record the {seat=}',
            deps=(flight_details, seat),
            usage=usage,
            usage_limits=usage_limits,
        )
        print(result.output)
        return result.all_messages()

async def main(test_prompt: str | None = None):
    user_prompt = test_prompt or input(
        '🤖 Hi! I am a flight search assistant. '
        'You can tell me the locations and dates of your trip and I will find the best flight for you\n'
        'You: '
    )
    conversation_history: list[ModelMessage] | None = None
    usage: RunUsage = RunUsage()

    # TODO: Add trip request tool and output validator

    # Start agent loop
    while user_prompt.strip().lower() not in QUIT_WORDS:
        trip, conversation_history = await infer_trip_request_via_trip_extractor_agent(
            user_prompt, conversation_history, usage
        )
        flights = await infer_flights_via_search_agent(trip, usage)

        if isinstance(flights, NoFlightFound):
            print(
                f'No flights from {trip.req_origin} to {trip.req_destination} '
                f'on {trip.req_date}.'
            )
            # nothing bought yet: let the user change the date, destination, etc.
            user_prompt = input(
                '🤖 Tell me what to change (e.g. a different date or destination), '
                f'or type {QUIT_WORDS} to stop\n'
                'You: '
            )
        else:
            display_flights(flights)
            flight = select_flight(flights)
            if flight is not None:
                seat = await infer_seat_via_seat_preference_agent(usage)
                booking_history = await infer_purchase_via_book_agent(usage, flight, seat)

                conversation_history.extend(booking_history)

            user_prompt = input(
                '🤖 Tell me what to do next (e.g. change dates or book another flight), '
                f'or type {QUIT_WORDS} to stop\n'
                'You: '
            )



if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
