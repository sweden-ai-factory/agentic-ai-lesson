"""OpenTelemetry / Jaeger instrumentation configuration.

Provides:
    log_default(), log_jaeger() and log_otel()
"""

import json
import os

import logfire
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanProcessor


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


def log_otel():
    """Run it via:
    docker run --rm -it -p 4318:4318 --name otel-tui docker://ymtdzzz/otel-tui:latest

    """
    os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4318'
    logfire.configure(send_to_logfire=False)
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)

def log_jaeger():
    """Run Jaeger using ./06_run_jaeger.sh script"""
    #
    # Jaeger only supports traces, not metrics, so only set the traces endpoint
    # to avoid errors about failing to export metrics.
    # Use port 4318 for HTTP, not 4317 for gRPC.
    # traces_endpoint = 'http://localhost:4318/v1/traces'
    traces_endpoint = 'http://localhost:5000/v1/traces'
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


def log_mlflow_old():
    """Configure MLFLOW"""
    # https://mlflow.org/docs/latest/genai/tracing/opentelemetry/genai-semconv/
    traces_endpoint = 'http://localhost:5000/v1/traces'

    # # Enable GenAI Semantic Convention format for OTLP export
    # os.environ["MLFLOW_ENABLE_OTEL_GENAI_SEMCONV"] = "true"
    # os.environ['OTEL_EXPORTER_OTLP_TRACES_ENDPOINT'] = traces_endpoint
    # os.environ['OTEL_EXPORTER_OTLP_TRACES_HEADERS'] = "flight_booking"

    # Enable both GenAI semconv format and dual export
    os.environ["MLFLOW_ENABLE_OTEL_GENAI_SEMCONV"] = "true"
    os.environ["MLFLOW_TRACE_ENABLE_OTLP_DUAL_EXPORT"] = "true"

    # Configure the MLflow tracking server URI and experiment ID
    os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5000"
    os.environ["MLFLOW_EXPERIMENT_ID"] = "flight_booking"

    import mlflow

    logfire.configure(send_to_logfire=False)

    mlflow.pydantic_ai.autolog()

    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("flight_booking")

    # logfire.instrument_pydantic_ai()
    # logfire.instrument_httpx(capture_request_body=True, capture_response_body=True)


def log_mlflow():
    import os

    traces_endpoint = 'http://localhost:5000/v1/traces'
    os.environ['OTEL_EXPORTER_OTLP_TRACES_ENDPOINT'] = traces_endpoint

    # 1. Build your own OTel provider with an OTLP exporter to MLflow
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    import mlflow
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("flight_booking")

    provider = TracerProvider()
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint="http://localhost:5000/v1/traces",
                headers={"x-mlflow-experiment-id": "flight_booking"}
            )
        )
    )
    trace.set_tracer_provider(provider)

    # 2. Configure logfire to NOT send to Logfire — it will use your provider
    import logfire
    logfire.configure(send_to_logfire=False)

    # 3. For Pydantic AI agent-level traces, add MLflow's native autolog
    # mlflow.pydantic_ai.autolog()
    #
    # or
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_request_body=True, capture_response_body=True)


def log_default():
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
