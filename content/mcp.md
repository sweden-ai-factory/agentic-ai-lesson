# 3. MCP Server

So far we have use the tools in the 

```{literalinclude} 04_mcp_server.py
:start-at: from mcp.server
:end-at: mcp = MCPServer("Demo")
```


```{literalinclude} 04_mcp_server.py
:start-at: mcp.tool()
:end-at: get_current_datetime
```


```{literalinclude} 04_mcp_client.py
:start-at: agent = Agent
:end-before: async def main()
```

## Exercise 3.1

Create your own tool for booking flights.

