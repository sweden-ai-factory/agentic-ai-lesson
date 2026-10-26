# Setup

## 0. Get LUMI access



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

## 3. Export the token

The scripts read the token from the `OPENAI_API_KEY` environment variable.

```bash
export OPENAI_API_KEY=<your-aitta-token>
```

Run this in the same terminal session you use for the scripts.