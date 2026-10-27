"""List the models currently available on the inference server.

The server is detected from MODEL_BASE_URL:

- Aitta (https://aitta-api.csc.fi/openai/v1): queries the Aitta REST API,
  which returns a HAL+JSON collection of workers (one entry per deployed
  model instance), and groups them by status. Equivalent to:

    curl -X 'GET' \
      'https://aitta-api.csc.fi/worker' \
      -H 'accept: application/hal+json' \
      -H 'Authorization: Bearer <token>'

- Any other OpenAI-compatible server (e.g. Berget,
  https://api.berget.ai/v1): queries the standard `GET /models` endpoint
  (https://api.berget.ai/v1/models/) and lists the models the server
  offers. Models that report capabilities are filtered to those that
  support function calling, which the agents in these lessons need.
  These servers do not expose a running/requested status, so all listed
  models are shown as available.

Run from content/hands-on:

    uv run 00_check_inference_server.py
"""

import os
from urllib.parse import urlsplit

import httpx2
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL_BASE_URL = "https://aitta-api.csc.fi/openai/v1"


def fetch_workers(client: httpx2.Client, api_root: str) -> list[dict]:
    """Fetch all Aitta workers, following pagination links if the collection is paged."""
    workers: list[dict] = []
    href = "/worker"
    while href:
        response = client.get(f"{api_root}{href}", headers={"accept": "application/hal+json"})
        response.raise_for_status()
        document = response.json()
        workers.extend(document.get("_embedded", {}).get("workers", []))
        href = document.get("_links", {}).get("next", {}).get("href")
    return workers


def fetch_models(client: httpx2.Client, base_url: str) -> list[str]:
    """Fetch model ids from the OpenAI-compatible `GET /models` endpoint.

    Models that report their capabilities are filtered to those that
    support function calling; models without capability data are kept
    as-is (a plain OpenAI-compatible server does not report capabilities).
    """
    response = client.get(f"{base_url}/models")
    response.raise_for_status()
    models = []
    for entry in response.json().get("data", []):
        capabilities = entry.get("capabilities")
        if capabilities is not None and not capabilities.get("function_calling"):
            continue
        models.append(entry["id"])
    return sorted(models)


def show_models(status: str, models: list[str]) -> None:
    print(f"{status} models ({len(models)}):")
    for model in models:
        print(f"  {model}")
    if not models:
        print("  <none>")


def main() -> None:
    token = os.getenv("OPENAI_API_KEY")
    if not token:
        raise SystemExit(
            "OPENAI_API_KEY is not set: copy content/hands-on/.env.example to content/hands-on/.env "
            "and add the access token for your inference server "
            "(for Aitta: https://aitta-auth.csc.fi/myToken)."
        )

    base_url = os.getenv("MODEL_BASE_URL", DEFAULT_MODEL_BASE_URL).rstrip("/")
    host = urlsplit(base_url).hostname or ""

    with httpx2.Client(
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    ) as client:
        if "aitta" in host:
            # The worker API lives at the server root, not under /openai/v1.
            api_root = f"https://{host}"
            print(f"Server: Aitta ({base_url})")
            print()
            workers = fetch_workers(client, api_root)
            running = sorted({worker["model"] for worker in workers if worker.get("status") == "running"})
            requested = sorted({worker["model"] for worker in workers if worker.get("status") == "requested"})
            show_models("Running", running)
            print()
            show_models("Requested", requested)
        else:
            print(f"Server: {base_url} (OpenAI-compatible API)")
            print()
            models = fetch_models(client, base_url)
            show_models("Running", models)


if __name__ == "__main__":
    main()
