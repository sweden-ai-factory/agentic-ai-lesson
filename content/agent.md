# Building an agent step by step

:::{questions}
- What is the least code you need to call an LLM and stream its answer?
- Why can't a plain language model tell you the time or remember what you just said?
- When an agent has several tools, how does it know which one to use?
- What actually happens when tools are "chained" together?
:::

:::{objectives}
- Build an agent gradually, adding a single idea at a time.
- Come away with a feel for four ideas (tools, memory, tool selection, and chaining) by running four small scripts.
:::

:::{highlight} python
:::

## 02: Time (tools and memory)

- Wrap the call in a real `You:` / `Agent:` conversation loop.
- Ask a plain model the time and it invents an answer, because it has no clock.
- `--enable_tools` gives it `get_current_datetime` to call, so it looks the time up instead of guessing.
- `--enable_history` feeds the past messages back, so follow-up questions work.

```{literalinclude} 02_time.py
```

## 03: Flight search (multiple tools)

- Tools and memory are now always on.
- Add a second, unrelated tool, `search_flights`, which reads a CSV of real routes.
- Ask about the time and it reaches for the clock; ask about Friday flights and it reaches for the search.
- One small change: `search_flights` now expects a concrete date, not a weekday.
- Now "any flights tomorrow?" can't be answered by a single tool.
- The agent calls `get_current_datetime` first to resolve "tomorrow", then hands that date to `search_flights`.
- That hand-off, where one tool's answer becomes the next tool's input, is chaining.

```{literalinclude} 03_flight_search.py
```

:::{discussion}
Discussion points
:::


## Summary

- Summary

## See also

- [pydantic-ai documentation](https://ai.pydantic.dev/)

:::{keypoints}
- Begin with the smallest call that works, then grow it one idea at a time.
- Tools let an agent act; history lets it remember.
- Given several tools, the agent picks the right one for each question.
- Chaining is when one tool's output feeds straight into another.
:::
