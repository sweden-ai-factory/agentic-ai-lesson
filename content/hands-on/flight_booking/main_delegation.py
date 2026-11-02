"""Agent-delegation version of the flight booking flow.

Where main.py hardcodes the pipeline (trip extractor -> flight search -> seat
preference -> booking), here a single orchestrator agent decides for itself
which specialist to call. The four agents from agents.py are registered as
sub-agents through the pydantic-ai-harness `SubAgents` capability, which
exposes them to the orchestrator as one `delegate_task(agent_name, task)` tool.

Each delegation runs the sub-agent with its own message history, so the task
must be self-contained. Deps are forwarded from the orchestrator run, which is
why `record_trip` below can set `deps.req_origin`/`req_destination` before the
search agent is delegated to (its output validator checks those values).

The booking agent's `deps_type` declares a (flight, seat) tuple for the
hand-off flow in main.py; the forwarded Deps go unused by it here, so the
booking task itself must spell out the chosen flight and seat.
"""

import logfire
from pydantic_ai import Agent, ModelMessage, RunContext
from pydantic_ai_harness import SubAgent, SubAgents

from .agents import (
    Deps,
    book_agent,
    search_agent,
    seat_preference_agent,
    trip_extractor_agent,
)
from .config import model, usage_limits

QUIT_WORDS = {'quit', 'exit'}

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
                        'Resolves the current date and time. '
                        'Then based on the travel date, origin and destination '
                        'of the trip requested, search flights.'
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
                SubAgent(
                    book_agent,
                    name='flight_booker',
                    description=(
                        'Books a chosen flight and seat, checking the travel '
                        'policy first, and finally purchasing a ticket.'
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
        "2. Delegate to `flight_searcher` with a task like 'Find me a flight "
        'from <origin> to <destination> on <date>.\'\n'
        '3. If it reports NoFlightFound, tell the user and ask what to change.\n'
        '4. Otherwise present the flights to the user and use ask_user to ask '
        'which one to buy. If the user wants to change the trip instead, start '
        'again from step 1 with their new request.\n'
        '5. Use ask_user to ask for their seat preference, then delegate their '
        'answer to `seat_extractor`. If it cannot extract a valid seat, ask '
        'the user to phrase it differently and delegate the new answer.\n'
        '6. Delegate the purchase to `flight_booker` with a self-contained task '
        'that includes every field of the chosen flight (flight number, '
        'origin, destination, date, departure and arrival times, price) and '
        'the chosen seat (row and seat letter), then confirm the purchase to '
        'the user.'
    ),
)


@orchestrator.tool_plain
def ask_user(question: str) -> str:
    """Ask the user a question and return their answer."""
    return input(f'🤖 {question} ')


async def main(test_prompt: str | None = None):
    user_prompt = test_prompt or input(
        '🤖 Hi! I am a flight search assistant. '
        'You can tell me the locations and dates of your trip and I will find the best flight for you\n'
        'You: '
    )
    conversation_history: list[ModelMessage] | None = None
    deps = Deps()

    while user_prompt.strip().lower() not in QUIT_WORDS:
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
            'or type "quit" to stop\nYou: '
        )


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
