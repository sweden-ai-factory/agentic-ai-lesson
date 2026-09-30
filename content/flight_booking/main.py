"""Main application flow for the flight booking system."""

from pydantic_ai import ModelMessage, RunUsage
from rich.prompt import Prompt

from .agents import (
    Deps,
    FlightDetails,
    NoFlightFound,
    SeatPreference,
    conversational_agent,
    search_agent,
    seat_preference_agent,
)
from .config import usage_limits


async def find_seat(usage: RunUsage) -> SeatPreference:
    message_history: list[ModelMessage] | None = None
    while True:
        answer = Prompt.ask('What seat would you like?')

        result = await seat_preference_agent.run(
            answer,
            message_history=message_history,
            usage=usage,
            usage_limits=usage_limits,
        )
        if isinstance(result.output, SeatPreference):
            return result.output
        else:
            print('Could not understand seat preference. Please try again.')
            message_history = result.all_messages()


async def buy_tickets(flight_details: FlightDetails, seat: SeatPreference):
    print(f'Purchasing flight {flight_details=!r} {seat=!r}...')


async def main():
    # user_prompt = Prompt.ask(
    #     "Hi! I am a flight search assistant. "
    #     "You can tell me the locations and dates of your trip and I will find the best flight for you\n>"
    # )
    user_prompt = "Flight from Helsinki to Stockholm tomorrow"
    conversation_history: list[ModelMessage] | None = None
    deps = Deps()
    usage: RunUsage = RunUsage()

    while True:
        # work out the trip the user wants (origin, destination, date), keeping the
        # conversation history so follow-ups like "make it next Monday" or "try Rome
        # instead" refine the previous request rather than starting from scratch
        user_result = await conversational_agent.run(
            user_prompt,
            deps=deps,
            message_history=conversation_history,
            usage_limits=usage_limits,
        )
        conversation_history = user_result.all_messages()
        trip = user_result.output
        deps.req_origin = trip.req_origin
        deps.req_destination = trip.req_destination

        result = await search_agent.run(
            f'Find me a flight from {trip.req_origin} to {trip.req_destination} on {trip.req_date}',
            deps=deps,
            usage=usage,
            usage_limits=usage_limits,
        )

        if isinstance(result.output, NoFlightFound):
            print(
                f'No flights from {trip.req_origin} to {trip.req_destination} '
                f'on {trip.req_date}.'
            )
        else:
            flights = result.output
            print(f'Found {len(flights)} flight(s):')
            for i, flight in enumerate(flights, start=1):
                print(
                    f'  {i}. {flight.flight_number}: {flight.origin} -> '
                    f'{flight.destination} on {flight.date}: '
                    f'{flight.departure_time} - {flight.arrival_time} for €{flight.price}'
                )
            answer = Prompt.ask(
                'Enter the number of the flight to buy, or press Enter to change your trip',
                choices=[str(i) for i in range(1, len(flights) + 1)] + [''],
                show_choices=False,
            )
            if answer.isdigit():
                flight = flights[int(answer) - 1]
                seat = await find_seat(usage)
                await buy_tickets(flight, seat)
                break

        # nothing bought yet: let the user change the date, destination, etc.
        user_prompt = Prompt.ask(
            'Tell me what to change (e.g. a different date or destination), '
            'or type "quit" to stop'
        )
        if user_prompt.strip().lower() in {'quit', 'exit'}:
            break


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
