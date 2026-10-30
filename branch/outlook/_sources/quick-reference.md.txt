# Quick Reference

The core terms of the workshop, grouped by the lesson that introduces them.

## {doc}`large-language-model`

- **Large language model (LLM)**: a model that predicts text one token at a time. Its output is
  stochastic and can be wrong even when it sounds confident. Example: `google/gemma-4-31b-it`, the
  model we used throughout the workshop.
- **Token**: the unit of text that the model reads and generates: fragments of words, punctuation
  and so on.
- **Pre-training and fine-tuning**: the model first learns general patterns from large amounts of
  text, then learns to follow instructions. Example: Poro 34B was pre-trained on about 1 trillion
  tokens of Finnish, English and code.
- **Training cut-off**: the model knows nothing about what happened after its training data ends.
  Example: a library released after the cut-off will not be suggested.
- **Inference server**: the service that runs the model and answers requests. Example: Aitta on
  LUMI, which we called with an `AsyncOpenAI` client.

## {doc}`agent-basics`

- **Agent**: a program that uses an LLM to decide how to act on its environment through tools.
- **Harness**: the code around the LLM that builds the prompt, runs tools and loops until the task
  is done. Example: Pydantic AI, which we used to build our agent. Claude Code and Codex are
  harnesses too.
- **Tool**: a function the agent can call. Its docstring and type hints tell the LLM when and how to
  use it. Example: `get_current_datetime`, `search_flights` and `book_flight`.
- **Tool call**: model output that asks the harness to run a tool. The harness runs it and returns
  the result to the model.
- **Stateless**: the LLM remembers nothing between requests, so the harness sends the full
  **conversation history** every time.
- **Tool chaining**: using the result of one tool call as input for the next. Example: resolving
  "next Monday" with `get_current_datetime` before calling `search_flights`.

## {doc}`mcp`

- **Model Context Protocol (MCP)**: an open standard for offering tools to any harness, regardless
  of the language the harness is written in.
- **MCP server, client and host**: the server provides the tools, the host (the harness) uses an MCP
  client to talk to it. The LLM never talks to the MCP server directly. Example: our
  `03_mcp_server.py` serving `get_current_datetime`, used by `03_mcp_client.py`.

## {doc}`adding-skills`

- **Skill**: a folder with a `SKILL.md` file of natural-language instructions, described by a `name`
  and a `description`. Example: the `travel-policy` skill with the rules for booking flights.
- **Progressive disclosure**: only the names and descriptions of skills are always in the context.
  The body is loaded when the LLM decides that the skill is relevant, by calling the
  `load_capability` tool.
- Skills guide the agent but do not enforce rules. Hard constraints belong in code.

## {doc}`adding-memory`

- **Short-term memory**: the conversation history. It is lost on restart and has to be kept short.
  Example: the time-of-day preference that the agent forgot after a restart.
- **Long-term memory**: notes that the agent writes, updates and deletes itself, for example in
  `MEMORY.md`, which the harness adds to every request.
- **Memory risks**: private data in the files, outdated notes, and injected text that affects all
  future sessions.

## {doc}`multi-agent`

placeholder

## {doc}`evaluation`

- **Observability**: recording what the agent does, not only what it answers. Example: Logfire's
  OpenTelemetry instrumentation of Pydantic AI.
- **Trace**: the recorded sequence of model requests and tool calls in one agent run. Example: a run
  that calls `get_current_datetime` more often than needed still gives the right answer, and only
  the trace shows it.
- **Metrics**: task success, tool usage, memory usage and cost.
- **Evaluation dataset**: a set of representative tasks for comparing versions of the agent, the way
  tests are used in traditional software.

## {doc}`security`

placeholder
