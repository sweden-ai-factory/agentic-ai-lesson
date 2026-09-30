"""Configuration for the flight booking application."""

import os

import logfire
from openai import AsyncOpenAI
from pydantic_ai import UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

USE_OPENTELEMETRY = False
#os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4318'
# Run it via:
# 	docker run --rm -it -p 4318:4318 --name otel-tui docker://ymtdzzz/otel-tui:latest

if USE_OPENTELEMETRY:
    logfire.configure(send_to_logfire=False)
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)
else:
    # 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
    logfire.configure(send_to_logfire='if-token-present')


# configure the inference endpoint
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", default="EMPTY"),
    base_url="https://aitta-api.csc.fi/openai/v1",
)

# choose the model from the inference endpoint
model_settings = ModelSettings(
    # temperature=0.0,
    timeout=10,
)
model = OpenAIChatModel(
    #"google/gemma-4-31b-it",
    "Qwen/Qwen3-Coder-Next",
    #"openai/gpt-oss-120b",
    provider=OpenAIProvider(openai_client=client),
    settings=model_settings,
)

# restrict how many requests this app can make to the LLM
usage_limits = UsageLimits(request_limit=15)
