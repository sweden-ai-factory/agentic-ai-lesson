"""Agent-delegation version of the flight booking flow.

Where main.py hardcodes the pipeline (conversational agent -> search agent ->
seat preference agent), here a single orchestrator agent decides for itself
which specialist to call. The three agents from agents.py are registered as
sub-agents through the pydantic-ai-harness `SubAgents` capability, which
exposes them to the orchestrator as one `delegate_task(agent_name, task)` tool.

Each delegation runs the sub-agent with its own message history, so the task
must be self-contained. Deps are forwarded from the orchestrator run, which is
why `record_trip` below can set `deps.req_origin`/`req_destination` before the
search agent is delegated to (its output validator checks those values).
"""

import logfire
from pydantic_ai import Agent, RunContext
from pydantic_ai_harness import SubAgent, SubAgents

from .agents import (
    Deps,
    search_agent,
    seat_preference_agent,
    trip_extractor_agent,
)
from .config import model, usage_limits

orchestrator = Agent(
    model,
    deps_type=Deps,
    capabilities=[
        SubAgents(
            agents=[
                SubAgent(
                    trip_extractor_agent,
                    name='trip_extractor',
                    description=(
                        'Extracts the origin, destination and travel date '
                        'from a user request'
                    ),
                ),
                SubAgent(
                    search_agent,
                    name='flight_searcher',
                    description=(
                        'Finds all flights between two locations on a given '
                        'date, sorted by price'
                    ),
                ),
                SubAgent(
                    seat_preference_agent,
                    name='seat_extractor',
                    description=(
                        "Extracts a seat preference (row number and seat "
                        "letter) from the user's answer"
                    ),
                ),
            ]
        )
    ],
    instructions=(
        'You are the orchestrator of a flight booking system. The user talks '
        'to you, and you delegate the specialist work to sub-agents with the '
        'delegate_task tool. Follow this workflow for a booking request:\n'
        '1. Delegate the user request verbatim to `trip_extractor` to get the '
        'origin, destination and travel date.\n'
        '2. Call record_trip with the origin and destination. This is required '
        'before searching: `flight_searcher` validates every flight it returns '
        'against the recorded trip.\n'
        "3. Delegate to `flight_searcher` with a task like 'Find me a flight "
        'from <origin> to <destination> on <date>.\'\n'
        '4. If it reports NoFlightFound, tell the user and ask what to change.\n'
        '5. Otherwise present the flights to the user and use ask_user to ask '
        'which one to buy. If the user wants to change the trip instead, start '
        'again from step 1 with their new request.\n'
        '6. Use ask_user to ask for their seat preference, then delegate their '
        'answer to `seat_extractor`. If it cannot extract a valid seat, ask '
        'the user to phrase it differently and delegate the new answer.\n'
        '7. Call buy_tickets with the chosen flight and seat, then confirm the '
        'purchase to the user.'
    ),
)


@orchestrator.tool
def record_trip(ctx: RunContext[Deps], origin: str, destination: str) -> str:
    """Record the requested origin and destination of the trip.

    Must be called before delegating to `flight_searcher`: it validates every
    flight it returns against these values.
    """
    ctx.deps.req_origin = origin
    ctx.deps.req_destination = destination
    return f'Recorded trip from {origin} to {destination}.'


@orchestrator.tool_plain
def ask_user(question: str) -> str:
    """Ask the user a question and return their answer."""
    return input(f'🤖 {question} ')


@orchestrator.tool_plain
def buy_tickets(flight_number: str, price: int, row: int, seat: str) -> str:
    """Purchase tickets for the chosen flight and seat."""
    print(f'Purchasing flight {flight_number} for €{price}, seat {row}{seat}...')
    return 'Tickets purchased.'


async def main(test_prompt: str | None = None):
    user_prompt = test_prompt or input(
        '🤖 Hi! I am a flight search assistant. '
        'You can tell me the locations and dates of your trip and I will find the best flight for you\n> '
    )
    conversation_history = None
    deps = Deps()

    while True:
        if user_prompt.strip().lower() in {'quit', 'exit'}:
            break

        # the orchestrator keeps the conversation history and decides itself
        # which sub-agent to delegate to at each step; the shared usage limits
        # apply across the whole agent tree
        with logfire.span('Orchestrator: delegate to sub-agents'):
            result = await orchestrator.run(
                user_prompt,
                deps=deps,
                message_history=conversation_history,
                usage_limits=usage_limits,
            )
            conversation_history = result.all_messages()
            print(f'🤖 {result.output}')

        user_prompt = input(
            '🤖 Tell me what to do next (e.g. book another trip), '
            'or type "quit" to stop '
        )


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
