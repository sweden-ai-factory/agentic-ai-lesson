"""Configuration for the flight booking application."""

import os

from openai import AsyncOpenAI
from pydantic_ai import UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

# Configures logfire / OpenTelemetry / Jaeger on import.
from . import config_logging

config_logging.log_default()

os.environ['PYDANTIC_AI_NO_BANNER'] = "1"


# the MCP server (03_mcp_server.py) that serves the flight search tools;
# 06_multi_agent_flight_booking.py launches it on this port
MCP_URL = f"http://127.0.0.1:{os.getenv('MCP_PORT', '8000')}/mcp"


# configure the inference endpoint
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", default="EMPTY"),
    base_url=os.getenv("MODEL_BASE_URL", "https://aitta-api.csc.fi/openai/v1"),
)

# choose the model from the inference endpoint
model_settings = ModelSettings(
    # temperature=0.0,
    timeout=30,
)
model = OpenAIChatModel(
    os.getenv("MODEL_NAME", "google/gemma-4-31b-it"),
    provider=OpenAIProvider(openai_client=client),
    settings=model_settings,
)

# restrict how many requests this app can make to the LLM
usage_limits = UsageLimits(request_limit=15)
