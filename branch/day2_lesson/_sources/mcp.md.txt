# 3. Model Context Protocol

In the previous sections, we have implemented our tools using Pydantic AI's
`@agent.tool_plain` decorator. Wrapping Python functions as tools using the harness
framework is straightforward, but comes with limitations. Suppose you are very happy
with your `get_current_datetime` tool, and would like to reuse it in another agent. To
do this, you would need to either import or simply copy the function from your existing
code. This further requires that you can edit the other agent's source code and that the
agent is written in the same language as the tools.

The [Model Context Protocol](https://modelcontextprotocol.io/) standard was developed to
enable harnesses (_hosts_ in MCP terminology) to access external resources provided by
an MCP server. The MCP host uses an MCP client to communicate with the server. This
means that the harness only needs to implement an MCP client to integrate with servers
that can be deployed locally or remotely in a variety of programming languages. This is
especially useful if you are using a pre-existing harness, such as a coding agent like
[Claude Code](https://code.claude.com/docs/en/overview) or
[Codex](https://learn.chatgpt.com/docs/codex/cli). These typically provide an MCP
client through which you can provide them with custom tools.

::::{tabs}
:::{group-tab} Framework-native
```{literalinclude} 03_flight_search.py
:lines: 12,15,30-31,34-47
```
:::

:::{group-tab} MCP
```{literalinclude} 04_mcp_server.py
:lines: 8-9,15-30
:::

## Exercise 3.1

Create your own tool for booking flights.

