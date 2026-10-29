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
from flight_booking.main import main  # noqa


def wait_for_mcp(process: subprocess.Popen, url: str = MCP_URL, timeout: float = 30.0):
    """Block until an MCP server responds at `url`.

    Any HTTP response (even an error status) means the server is up; only
    connection failures are retried. The URL is checked before the process
    state, so an already-running MCP server (e.g. from lesson 04) on the same
    port also counts. Raises if the process dies or the timeout expires.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            httpx2.get(url, timeout=1.0)
            return
        except httpx2.TransportError:
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
args = parser.parse_args()

mcp_process = subprocess.Popen(
    [sys.executable, "03_mcp_server.py"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
with logfire.span("Wait for MCP"):
    wait_for_mcp(mcp_process)

try:
    asyncio.run(main(random.choice(TEST_PROMPTS) if args.test else None))
finally:
    mcp_process.terminate()
