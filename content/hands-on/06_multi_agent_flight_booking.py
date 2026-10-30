import argparse
import asyncio
import random
import subprocess
import sys
import time

import httpx2
import logfire
from dotenv import load_dotenv

load_dotenv()


from flight_booking.config import MCP_URL  # noqa
from flight_booking.main import main as main_handoff  # noqa
from flight_booking.main_delegation import main as main_delegation  # noqa


def wait_for_mcp(url: str = MCP_URL, timeout: float = 30.0) -> subprocess.Popen | None:
    """Ensure an MCP server responds at `url`, spawning one if needed.

    If the port is already in use (e.g. by the MCP server from lesson 04),
    no process is spawned and None is returned. Otherwise a new server is
    started and the returned process should be terminated by the caller.

    Any HTTP response (even an error status) means the server is up; only
    connection failures are retried. Raises if the spawned process dies or
    the timeout expires.
    """
    try:
        httpx2.get(url, timeout=1.0)
        return None
    except httpx2.TransportError:
        pass

    process = subprocess.Popen(
        [sys.executable, "03_mcp_server_solution.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            httpx2.get(url, timeout=1.0)
            return process
        except httpx2.TransportError as e:
            pass
        if process.poll() is not None:
            raise RuntimeError(
                f"MCP server exited early with code {process.returncode}"
            )
        time.sleep(0.3)
    raise TimeoutError(f"MCP server not ready at {url} within {timeout:.0f}s")


TEST_PROMPTS = [
    'Flight from Helsinki to Stockholm tomorrow',
    'I want to fly from Paris to Rome next Friday',
    'Book me a trip from Warsaw to Vienna in three days',
]

parser = argparse.ArgumentParser(description='Multi-agent flight booking demo')
parser.add_argument(
    '--test',
    action='store_true',
    help='run with a random test prompt instead of asking the user',
)
parser.add_argument(
    '-p',
    '--pattern',
    choices=['handoff', 'delegation'],
    default='handoff',
    help=(
        'multi-agent pattern to run: "handoff" is the programmatic agent '
        'hand-off (flight_booking/main.py), "delegation" is agent delegation '
        'through the SubAgents capability (flight_booking/main_delegation.py)'
    ),
)
args = parser.parse_args()

with logfire.span("Wait for MCP"):
    mcp_process = wait_for_mcp()

try:
    main = main_delegation if args.pattern == 'delegation' else main_handoff
    asyncio.run(main(random.choice(TEST_PROMPTS) if args.test else None))
finally:
    if mcp_process is not None:
        mcp_process.terminate()
