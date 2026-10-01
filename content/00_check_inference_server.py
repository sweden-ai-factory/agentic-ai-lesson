"""List the models currently running on the Aitta inference server.

Queries the Aitta REST API, which returns a HAL+JSON collection of workers
(one entry per deployed model instance). Equivalent to:

    curl -X 'GET' \
      'https://aitta-api.csc.fi/worker' \
      -H 'accept: application/hal+json' \
      -H 'Authorization: Bearer <token>'

Run from the repository root:

    uv run content/00_check_inference_server.py
"""

import os

import httpx2
from dotenv import load_dotenv

load_dotenv()

AITTA_API_URL = "https://aitta-api.csc.fi"


def fetch_workers(client: httpx2.Client) -> list[dict]:
    """Fetch all workers, following pagination links if the collection is paged."""
    workers: list[dict] = []
    href = "/worker"
    while href:
        response = client.get(href, headers={"accept": "application/hal+json"})
        response.raise_for_status()
        document = response.json()
        workers.extend(document.get("_embedded", {}).get("workers", []))
        href = document.get("_links", {}).get("next", {}).get("href")
    return workers


def main() -> None:
    token = os.getenv("OPENAI_API_KEY")
    if not token:
        raise SystemExit(
            "OPENAI_API_KEY is not set: copy content/.env.example to content/.env "
            "and add your Aitta token (https://aitta-auth.csc.fi/myToken)."
        )

    with httpx2.Client(
        base_url=AITTA_API_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    ) as client:
        workers = fetch_workers(client)

    running = sorted({worker["model"] for worker in workers if worker.get("status") == "running"})

    print(f"Running models ({len(running)}):")
    for model in running:
        print(f"  {model}")
    if not running:
        print("  <none>")


if __name__ == "__main__":
    main()
