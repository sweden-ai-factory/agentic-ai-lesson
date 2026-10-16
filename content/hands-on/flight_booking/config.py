"""Configuration for the flight booking application."""

import json
import os

import logfire
from openai import AsyncOpenAI
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanProcessor
from pydantic_ai import UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

# INSTRUMENTATION = ""


# INSTRUMENTATION = "OTEL"
# Run it via:
# 	docker run --rm -it -p 4318:4318 --name otel-tui docker://ymtdzzz/otel-tui:latest

INSTRUMENTATION = "JAEGER"
# Run using ./07_run_jaeger.sh script

os.environ['PYDANTIC_AI_NO_BANNER'] = "1"


def _filter_sse(text: str) -> str:
    """Extract the JSON payloads from a text/event-stream body."""
    data_lines = [
        line.removeprefix('data:').strip()
        for line in text.splitlines()
        if line.startswith('data:')
    ]
    return '\n'.join(data_lines) if data_lines else text


class GenAiHttpBodyProcessor(SpanProcessor):
    """Copy captured HTTP bodies into gen_ai attributes.

    The httpx instrumentation (capture_all=True) stores request and response
    bodies under http.request.body.text / http.response.body.text, which Jaeger
    only shows in the generic Tags view. This processor copies them into
    gen_ai.input.messages / gen_ai.output.messages, the format Jaeger's GenAI
    tab renders as conversation messages. SSE envelopes are filtered down to
    their JSON payloads.

    It is passed to logfire.configure(additional_span_processors=[...]), so it
    runs before the exporting processor: enriching the span here is picked up
    when the span is exported. The public SDK has no way to modify a span in
    on_end, hence the private _attributes replacement.
    """

    def on_end(self, span: ReadableSpan) -> None:
        attributes = span.attributes or {}
        request_body = attributes.get('http.request.body.text')
        response_body = attributes.get('http.response.body.text')
        if not (request_body or response_body):
            return
        attributes = dict(attributes)
        if request_body:
            attributes['gen_ai.input.messages'] = json.dumps(
                [{'role': 'user', 'parts': [{'type': 'text', 'content': request_body}]}]
            )
        if response_body:
            attributes['gen_ai.output.messages'] = json.dumps(
                [
                    {
                        'role': 'assistant',
                        'parts': [{'type': 'text', 'content': _filter_sse(response_body)}],
                    }
                ]
            )
        span._attributes = attributes


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
        service_name="flight_booking",
        # Sending to Logfire is on by default regardless of the OTEL env vars.
        # Keep this line here if you don't want to send to both Jaeger and Logfire.
        send_to_logfire=False,
        # Copy captured HTTP bodies into gen_ai attributes so that they show
        # up in Jaeger's GenAI tab instead of only in the Tags view.
        additional_span_processors=[GenAiHttpBodyProcessor()],
    )
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_request_body=True, capture_response_body=True)
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


# the MCP server (04_mcp_server.py) that serves the flight search tools;
# 07_multi_agent_flight_booking.py launches it on this port
MCP_PORT = 8111
MCP_URL = f"http://127.0.0.1:{MCP_PORT}/mcp"


# configure the inference endpoint
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", default="EMPTY"),
    base_url=os.getenv("MODEL_BASE_URL", "https://aitta-api.csc.fi/openai/v1"),
)

# choose the model from the inference endpoint
model_settings = ModelSettings(
    # temperature=0.0,
    timeout=10,
)
model = OpenAIChatModel(
    os.getenv("MODEL_NAME", "google/gemma-4-31b-it"),
    provider=OpenAIProvider(openai_client=client),
    settings=model_settings,
)

# restrict how many requests this app can make to the LLM
usage_limits = UsageLimits(request_limit=15)
