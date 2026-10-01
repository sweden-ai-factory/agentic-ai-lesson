"""Configuration for the flight booking application."""

import os

import logfire
from openai import AsyncOpenAI
from pydantic_ai import UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

INSTRUMENTATION = ""


# INSTRUMENTATION = "OTEL"
# Run it via:
# 	docker run --rm -it -p 4318:4318 --name otel-tui docker://ymtdzzz/otel-tui:latest

# INSTRUMENTATION = "JAEGER"
# docker run --rm -p 16686:16686 -p 4318:4318  docker://jaegertracing/all-in-one:latest

os.environ['PYDANTIC_AI_NO_BANNER'] = "1"
if INSTRUMENTATION == "OTEL":
    os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4318'
    logfire.configure(send_to_logfire=False)
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)
elif INSTRUMENTATION == "JAEGER":
    # Jaeger only supports traces, not metrics, so only set the traces endpoint
    # to avoid errors about failing to export metrics.
    # Use port 4318 for HTTP, not 4317 for gRPC.
    traces_endpoint = 'http://localhost:4318/v1/traces'
    os.environ['OTEL_EXPORTER_OTLP_TRACES_ENDPOINT'] = traces_endpoint
    logfire.configure(
        # Setting a service name is good practice in general, but especially
        # important for Jaeger, otherwise spans will be labeled as 'unknown_service'
        service_name='my_logfire_service',
        # Sending to Logfire is on by default regardless of the OTEL env vars.
        # Keep this line here if you don't want to send to both Jaeger and Logfire.
        send_to_logfire=False,
    )
else:
    # 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
    logfire.configure(send_to_logfire='if-token-present')

    logfire.instrument_pydantic_ai()
    logfire_handler = logfire.LogfireLoggingHandler()

    import logging
    # logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])
    # logger = logging.getLogger(__name__)
    urllib3_filter = logging.Filter('urllib3')
    # Disable urllib3 debug logs on the fallback handler
    # (by default, writing to `sys.stderr`):
    logfire_handler.fallback.addFilter(lambda record: not urllib3_filter.filter(record))

    logfire_handler = logfire.LogfireLoggingHandler()
    urllib3_filter = logging.Filter('urllib3')
    # Disable urllib3 debug logs on the fallback handler
    # (by default, writing to `sys.stderr`):
    logfire_handler.fallback.addFilter(lambda record: not urllib3_filter.filter(record))
    logging.basicConfig(handlers=[logfire_handler], level=logging.DEBUG)


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
    "google/gemma-4-31b-it",
    # "Qwen/Qwen3-Coder-Next",
    # "openai/gpt-oss-120b",
    provider=OpenAIProvider(openai_client=client),
    settings=model_settings,
)

# restrict how many requests this app can make to the LLM
usage_limits = UsageLimits(request_limit=15)
