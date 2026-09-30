# Building an agent step by step

## 1. Install dependencies

The project is managed with [uv](https://docs.astral.sh/uv/). Install uv if you
don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create venv

```bash
uv sync
```

## 2. Get an Aitta access token

1. Go to <https://aitta-auth.csc.fi/myToken> (also reachable from
   <https://aitta.csc.fi/> → **Generate token**).
2. Log in with your account.
3. Generate a token and copy it.

## 3. Provide the token

The scripts read the token from the `OPENAI_API_KEY` environment variable.

Either export it in the terminal session you use for the scripts:

```bash
export OPENAI_API_KEY=<your-aitta-token>
```

Or copy `.env.example` to `.env` in the repository root and fill in your token
(the scripts load it automatically via `python-dotenv`):

```bash
cp .env.example .env
# then edit .env and set OPENAI_API_KEY=<your-aitta-token>
```

`.env` is gitignored, so your token stays out of version control.

## 4. Run the lessons

Run everything with `uv run` from the repository root so the right environment is used.

### 01 – Hello world

The smallest possible call: one model, one `Agent`, one streamed reply.

```bash
uv run python content/01_hello_world.py
```

### 02 – Time (tools and memory)

A `You:` / `Agent:` chat loop. Flags turn features on so you can see the
difference:

```bash
uv run python content/02_time.py                              # plain model, invents the time
uv run python content/02_time.py --enable_tools               # can look the time up
uv run python content/02_time.py --enable_tools --enable_history   # also remembers the conversation
```

### 03 – Flight search (multiple tools)

Adds a second tool (`search_flights`) and shows tool selection and chaining. Type
`quit`, `exit`, or an empty line to stop.

```bash
uv run python content/03_flight_search.py
```

### 04 – MCP server and client

Here the tools live in a separate MCP server. Start the server first, then the client in a **second terminal** (remember to export `OPENAI_API_KEY` there too).

Terminal 1 – server (listens on `http://localhost:8000/mcp`):

```bash
uv run python content/04_mcp_server.py
```

Terminal 2 – client:

```bash
uv run python content/04_mcp_client.py
```

### 05 – Skills

Adds a travel-policy skill on top of the MCP tools. It also connects to the MCP
server from lesson 04, so keep that server running (Terminal 1 above).

```bash
uv run python content/05_skills.py                    # fresh session each run
uv run python content/05_skills.py --remember-history # persists history to travel_history.json
```