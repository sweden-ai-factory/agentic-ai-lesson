import asyncio
import subprocess
import time

import logfire
from dotenv import load_dotenv

load_dotenv()
logfire.install_auto_tracing(
    modules=["flight_booking", "flight_booking.main"], min_duration=0.01
)


from flight_booking.main import main  # noqa

mcp_process = subprocess.Popen(
    ["uv", "run", "mcp", "run", "04_mcp_server.py", "--transport", "streamable-http"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
# time.sleep(2)
asyncio.run(main())

mcp_process.terminate()
