# 5. Memory

- Motivation: LLMs have no memory of their own
  - The API is stateless: every request starts from nothing
  - "Memory in chat is resending information, not the model remembering
  - Exercise 2.2: the interactive chat only worked because we sent the full history each time

- Short-term memory: the conversation history

- Strategies when the history gets too long

The following adds memory to our agent: `Memory(FileStore(MEMORY_DIR))`

```{literalinclude} hands-on/06_memory.py
:start-at: agent = Agent(
:end-before: async def main():
```

Try it out with the following:

```bash
uv run 06_memory.py
```

- Risks
  - Privacy: what gets stored, where, and who can read it
  - Stale or wrong memories that the agent keeps trusting
  - Memory poisoning: injected text saved as "memory" affects all future sessions
