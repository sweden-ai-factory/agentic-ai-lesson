import asyncio
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
            time.sleep(0.1)
    raise TimeoutError(f"MCP server not ready at {url} within {timeout:.0f}s")


mcp_process = subprocess.Popen(
    [sys.executable, "04_mcp_server.py", "--port", str(MCP_PORT)],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
wait_for_mcp(mcp_process)
try:
    asyncio.run(main())
finally:
    mcp_process.terminate()
