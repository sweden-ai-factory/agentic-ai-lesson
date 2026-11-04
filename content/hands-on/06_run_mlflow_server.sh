#!/bin/bash
alias mlflow='uvx mlflow'

export MLFLOW_ENABLE_OTEL_GENAI_SEMCONV=true

# mlflow experiments create -n flight_booking
mlflow server --host 127.0.0.1 --port 5000
