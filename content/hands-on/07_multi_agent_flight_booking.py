import argparse
import asyncio
import random
import subprocess
import sys
import time

import httpx
import logfire
from dotenv import load_dotenv

load_dotenv()
logfire.install_auto_tracing(
    modules=["flight_booking", "flight_booking.main"], min_duration=0.01
)


from flight_booking.config import MCP_PORT, MCP_URL  # noqa
from flight_booking.main import main  # noqa


def wait_for_mcp(process: subprocess.Popen, url: str = MCP_URL, timeout: float = 30.0):
    """Block until the MCP server responds at `url`.

    Any HTTP response (even an error status) means the server is up; only
    connection failures are retried. Raises if the process dies or the
    timeout expires.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"MCP server exited early with code {process.returncode}"
            )
        try:
            httpx.get(url, timeout=1.0)
            return
        except httpx.TransportError:
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
    [sys.executable, "04_mcp_server.py", "--port", str(MCP_PORT)],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
with logfire.span("Wait for MCP"):
    wait_for_mcp(mcp_process)

try:
    asyncio.run(main(random.choice(TEST_PROMPTS) if args.test else None))
finally:
    mcp_process.terminate()
