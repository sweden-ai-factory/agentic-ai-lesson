# 0. Setup

:::{objectives}

- Get access to the Aitta inference service and an API token.
- Install the course code and its Python dependencies with `uv`.
- Configure the token and model settings in a `.env` file.
- Check that you can reach the model before the first lesson.
:::

## What you need

- A laptop running Linux, macOS, or Windows (WSL recommended on Windows).
- A terminal and a code editor.
- [git](https://git-scm.com/) to download the course material.
- A LUMI account, used to log in to [Aitta](https://aitta.csc.fi/), the CSC
  inference service that runs the LLMs on the LUMI supercomputer.
- Optional: [Docker](https://docs.docker.com/get-docker/) or [Podman](https://podman.io/docs/installation) for viewing traces with
  Jaeger in the multi-agent episode. The script that starts Jaeger is a bash script,
  so it doesn't run in plain PowerShell on Windows. That's okay: tracing is optional
  and you can follow the episode without it.

You do **not** need to install Python yourself: `uv` downloads the right version
(Python 3.14) automatically.

::::{admonition} Alternative: noppe (no installation)
:class: dropdown

If you cannot install the course software on your laptop, you can use
[noppe](https://noppe.csc.fi/), a CSC service that runs JupyterLab in your browser.
The course material and all Python packages are already installed there. You
still need LUMI access and an Aitta token (steps 0 and 3).

1. Go to <https://noppe.csc.fi/> and log in with the same account you use for
   the Aitta token (step 3), for example **MyAccessID**.
2. Click **Join workspace** and enter the **join code** we sent you by email.
3. Start the application **agentic-ai-lesson**. JupyterLab opens in
   `agentic-ai-lesson/content/hands-on`.
4. Skip steps 1 and 2 below and continue with step 3. Run the commands in a
   JupyterLab terminal (**File → New → Terminal**). It starts in
   `content/hands-on`, so skip the `cd content/hands-on` commands in steps 4 and 5.
   When an episode needs a second terminal, for example for the MCP server, open
   another one the same way.

:::{warning}
Nothing you change in noppe is kept when your session restarts or ends. Every
time you start the application, you get a fresh copy of the course material:

- **Your `.env` is gone.** Create it again as in step 4, so keep your token in a
  safe place, such as a password manager.
- **Your own code is gone.** Before you stop, download the files you want to
  keep: right-click them in the file browser and choose **Download**.
:::

::::

## 0. Get LUMI access

You log in to Aitta with your LUMI account, and your Aitta token is tied to a
LUMI project. You need to be a member of **any** LUMI project:

- If you have been added to the training project (**465002387**), use that one.
- If not, any other LUMI project you belong to works just as well. Aitta does not
  bill token usage to the project yet, so it doesn't matter which one you pick.

## 1. Get the course material

```bash
git clone https://github.com/sweden-ai-factory/agentic-ai-lesson.git
cd agentic-ai-lesson
```

## 2. Install dependencies

The project is managed with [uv](https://docs.astral.sh/uv/). Install uv if you
don't have it:

::::{tabs}

:::{group-tab} Linux / macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

:::

:::{group-tab} Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

:::

::::

If these don't work for you, the
[uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)
lists other options, such as Homebrew, WinGet, or pip.

Open a new terminal so `uv` is on your `PATH`, then create the virtual environment
from the repository root:

```bash
uv sync
```

This installs Python 3.14 if needed and all packages used in the hands-on examples
(Pydantic AI, the OpenAI client, MCP, ...).

## 3. Get an Aitta access token

1. Go to <https://aitta-auth.csc.fi/myToken> (also reachable from
   <https://aitta.csc.fi/> → **Generate token**).
2. Log in with the account you use for LUMI. For the course project this is
   **MyAccessID**; if you use another LUMI project, log in the way you normally
   access that project.
3. Pick a LUMI project: the course project **465002387** if you are a member,
   otherwise any other LUMI project you belong to (see step 0).
4. Generate a token and copy it.

:::{warning}
Treat the token like a password: don't paste it into chats, commit it to git, or
share it in screenshots. Tokens expire, so generate a new one if requests suddenly
fail with `401 Unauthorized`.
:::

### Revoking a token

Aitta tokens are valid for 90 days. A token stops working earlier if the LUMI
project it is tied to ends or your user account is closed. Revoke your token
yourself when you no longer need it, for example after the course, or right away
if it has leaked (committed to git, shared in a chat, ...):

1. Go to <https://aitta-auth.csc.fi/idp/profile/userprofile> and log in.
2. Open **Connected Organizations**.
3. Find **Aitta Token Generator** and click **Revoke now**.
4. If you still need access, generate a new token (see above) and update your
   `.env`.

A leaked token must always be revoked: removing it from git in a new commit is not
enough, because it stays in the history.

## 4. Configure your environment

All examples live in `content/hands-on/` and read their settings from environment
variables. The easiest way is a `.env` file, which the scripts load automatically:

```bash
cd content/hands-on
cp .env.example .env
```

Open `.env` and fill in your token:

```bash
OPENAI_API_KEY=<your-aitta-token>
MODEL_NAME=google/gemma-4-31b-it
MODEL_BASE_URL=https://aitta-api.csc.fi/openai/v1
#MCP_PORT=8000
```

| Variable         | Meaning                                                 |
| ---------------- | ------------------------------------------------------- |
| `OPENAI_API_KEY` | Your Aitta token (Aitta has an OpenAI-compatible API).  |
| `MODEL_NAME`     | Which model to use. See step 5 for available models.    |
| `MODEL_BASE_URL` | Where the API lives. Change only to use another server. |
| `MCP_PORT`       | Port of the local MCP server used from episode 3 on.    |

`.env` is gitignored, so your token stays out of version control.

:::{admonition} Alternative: export in the shell
:class: dropdown

Instead of a `.env` file you can export the variables in the terminal you use for
the scripts. This has to be repeated in every new terminal.

```bash
export OPENAI_API_KEY=<your-aitta-token>
```

:::

## 5. Check that everything works

Run all commands from `content/hands-on/`. If you are not already there, change
into it from the repository root:

```bash
cd content/hands-on
```

First, list the models currently running on Aitta. This also checks that your
token is valid:

```bash
uv run 00_check_inference_server.py
```

You should see a list of running models. Make sure the `MODEL_NAME` in your `.env`
is one of them.

Aitta runs its models on LUMI, so when LUMI is down (for example during a
maintenance break) no models are available. The script then tells you so
instead of listing models. Your token is still fine; try again later.

If this was successful, send a first prompt to the model:

```bash
uv run 01_hello_world.py
```

If the answer is streamed to your terminal, you are ready for the course.

## Troubleshooting

| Problem                                          | Fix                                                                                                                       |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| `OPENAI_API_KEY is not set`                      | The `.env` file is missing or not in `content/hands-on/`. Check step 4.                                                   |
| `401 Unauthorized`                               | The token is wrong or has expired. Generate a new one (step 3).                                                           |
| `503 Service Unavailable`                        | Your token is fine, but LUMI is down, so Aitta cannot serve models. Try again later.                                      |
| `uv: command not found`                          | Open a new terminal after installing `uv`, or see the [uv docs](https://docs.astral.sh/uv/getting-started/installation/). |
| Connection errors in the MCP examples            | Start the MCP server in a **second terminal** (see {doc}`mcp`). If port 8000 is taken, set `MCP_PORT`.                    |
| `pydantic_ai.exceptions.UnexpectedModelBehavior` or empty responses from agent [^1] | Run `uv run 00_check_inference_server.py` and change to a different model.                                               |

[^1]: See [issue #43](https://github.com/sweden-ai-factory/agentic-ai-lesson/issues/43) for typical known models where this happens and how these output look like.
