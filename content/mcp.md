# 3. Model Context Protocol

In the previous sections, we have implemented our tools using Pydantic AI's
`@agent.tool_plain` decorator. Wrapping Python functions as tools using the harness
framework is straightforward, but comes with limitations. Suppose you are very happy
with your `get_current_datetime` tool, and would like to reuse it in another agent or
share it with other people in your company. To do this, you would need to either import
or simply copy the function from your existing code. This further requires that you can
edit the other agent's source code and that the agent is written in the same language as
the tools.

The [Model Context Protocol](https://modelcontextprotocol.io/) standard was developed to
enable harnesses (_hosts_ in MCP terminology) to access external resources provided by
an MCP server. The MCP host uses an MCP client to communicate with the server. This
means that the harness only needs to implement an MCP client to integrate with servers
that can be deployed locally or remotely in a variety of programming languages. This is
especially useful if you are using a pre-existing harness, such as a coding agent like
[Claude Code](https://code.claude.com/docs/en/overview) or
[Codex](https://learn.chatgpt.com/docs/codex/cli). These typically provide an MCP client
through which you can provide them with custom tools.

In the tabs below, you can compare implementing a tool directly in our agent, as you did
in the previous sections, with implementing it via an MCP server. The only changes are
to initialize a new MCP server with `mcp = MCPServer("Demo")` (named `Demo` in this
case) and to change the decorator to `@mcp.tool()`.

::::{tabs}
:::{group-tab} Framework-native
```{literalinclude} hands-on/02b_flight_search.py
:lines: 12,15,30-31,34-47
```
:::

:::{group-tab} MCP
```{literalinclude} hands-on/03_mcp_server.py
:lines: 10-11,20-35
```
:::
::::

As the name says, the MCP server is a server that needs to be started before we can use
it. You will do this in Exercise 3.1 with the following command. The server uses the
`streamable-http` transport, which runs it as an HTTP service that clients connect to
over the network.

```bash
uv run 03_mcp_server.py
```

This will start the MCP server locally at the address `http://127.0.0.1:8000/mcp`.

But how do we connect the MCP server to our agent? In the code snippet below, we add a
new `MCP` capability to the agent. This is all that is needed: the agent will now be
able to use the tools of the MCP server.

```{literalinclude} hands-on/03_mcp_client.py
:start-at: agent = Agent(
:end-before: async def main():
```


## Exercise 3.1

:::{exercise}
Before modifying the MCP server, let's see how the existing `get_current_datetime` tool
works. Start the MCP server in a new terminal from the `hands-on` directory:

```bash
uv run 03_mcp_server.py
```

You can try opening `http://127.0.0.1:8000/mcp` in your browser. Do not worry if it
gives you some message about a missing session id. The server works, but the request
needs to contain more information than what your browser sends. You should also see some
message in the terminal where you started the server.

Leave it running, and in a second terminal start the agent from the `hands-on` directory
(it reads your token from `.env`, as in the previous episodes):

```bash
uv run 03_mcp_client.py
```

Ask the agent something like "What time is it?" and look at the log of the terminal
where your agent is running. How many times is the MCP server called, and when does
the LLM come into play?
:::

:::{solution}
You likely saw the following steps. This is what they mean:

1. **`agent run`**: your prompt starts an agent run in the harness.
2. **`server/discover`**: the harness asks the MCP server for its supported protocol
   versions, capabilities and identity.
3. **`tools/list`**: the harness fetches the server's tools through `MCPToolset`.
4. **First `chat`**: the LLM gets your question and the tool definitions, and responds
   with a call to `get_current_datetime`. The inference server parses the tool call from
   the LLM's output and returns it to the harness as a structured response.
5. **`running tool` → `tools/call` → `MCP send`**: the harness calls the tool on the MCP
   server.
6. **Second `chat`**: the LLM gets the tool result (plus the tool definitions again) and
   writes the answer.

The MCP server is called three times (discover, list, call), and the LLM twice.

The key point: the LLM never interacts with the MCP server directly. The harness
coordinates everything. Before the LLM is called for the first time, the harness has
already fetched the server's tools and added them to the LLM's context together with
your prompt.
:::


## Exercise 3.2

:::{exercise}
In this exercise, start expanding the MCP server given in `hands-on/03_mcp_server.py` to
add your own tool.

Add a tool `book_flight` to `03_mcp_server.py` that takes a flight number (`flight_no`,
as in `data/flights.csv`), a passenger name and a date, and appends the booking as a new
row to `data/bookings.csv` using pandas. Add it above the `if __name__ == "__main__":`
block at the end of the file, which starts the server.

Some hints to help you get started:

- Have a look at the `search_flights` tool for the decorator and docstring.
- The docstring and type hints become the tool description that is added to the context
  of the LLM.
- `pd.DataFrame.to_csv` can append with `mode="a"`. Only write the header if the file
  doesn't exist yet.

You can test it as follows:

1. Restart the MCP server. It doesn't pick up code changes automatically.
2. Start the agent and ask: "Book a flight from Helsinki to Stockholm next Monday for
   Linus Torvalds."
3. Check the log: which tools does the agent call, and in what order?
4. Check the file: `cat data/bookings.csv`

Think about the following:

- Ask "Book me a flight to Stockholm tomorrow" without giving a name. Does the agent ask
  for it, or make one up?
- This tool might have more consequences than the search flights tool. Should the agent
  ask for confirmation before booking?
:::

:::{solution}
```{literalinclude} hands-on/03_mcp_server_solution.py
:start-after: model solution
:end-before: if __name__ == "__main__":
```

You can also try out an MCP server with the model solution by stopping the old MCP
server and starting a new one with the following command:

```bash
uv run 03_mcp_server_solution.py
```
:::

:::{exercise} Going further (optional)
- Return an error if the flight doesn't exist in `flights.csv` or doesn't fly on that
  date.
- Add a `list_bookings` tool that shows the bookings for a passenger.
- Add a `cancel_booking` tool.
- Connect your MCP server to another harness you use, for example a coding agent or your
  IDE. Look up how it registers MCP servers, point it at `http://127.0.0.1:8000/mcp` and
  ask it something only your tools can answer. The same server now works in a harness
  you did not write.
:::

## Using existing MCP servers

You don't have to write every MCP server yourself. Many services already provide one,
and connecting to it works the same way as connecting to your own server. For example,
the LUMI AI Factory runs a [public MCP
server](https://docs.lumi-supercomputer.eu/laif/software/agent-infrastructure/) at
`https://lumi-aif-agents.2.rahtiapp.fi/mcp`. Its tools search the LUMI documentation and
report the status of LUMI services. To give our agent access to it, add a second `MCP`
capability:

```python
agent = Agent(
    model,
    capabilities=[
        MCP(url="http://127.0.0.1:8000/mcp"),
        MCP(url="https://lumi-aif-agents.2.rahtiapp.fi/mcp"),
    ],
)
```

Only connect to MCP servers you trust. The tool descriptions a server returns go
straight into the LLM's context, so a malicious server can try to steer your agent, and
its tools can do whatever the server's code does. More on security in the [security
section](security.md).
