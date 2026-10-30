# 9. Outlook

## Recap: test yourself

Try to answer before opening the solutions. The {doc}`quick-reference` lists all the terms.

### {doc}`large-language-model`

:::{exercise}
In [Exercise 1.1](large-language-model.md#exercise-11-use-an-llm) you sent the same prompt as the
instructors but got a different reply. Why?
:::

:::{solution}
LLM output is stochastic: the model predicts one token at a time and samples from the options.
:::

### {doc}`agent-basics`

:::{exercise}
Why did "What is the time in the city that the instructor lives in?" only work with
`--enable_history` ([Exercise 2.3](agent-basics.md#exercise-23-enable-conversation-history))?
:::

:::{solution}
The LLM is stateless. Only with history does the harness resend the earlier prompt.
:::

### {doc}`mcp`

:::{exercise}
What is the benefit of MCP servers?
:::

:::{solution}
MCP is an open standard: you write a tool once and any harness can use it, whatever language it is
written in. Example: the `book_flight` server from [Exercise 3.2](mcp.md#exercise-32) also works in a
coding agent or your IDE.
:::

### {doc}`adding-skills`

:::{exercise}
Does your `booking-confirmation` skill
([Exercise 4.2](adding-skills.md#exercise-42-write-your-own-skill)) guarantee that the agent always
confirms?
:::

:::{solution}
No. Skills guide but do not enforce. Hard constraints belong in code, for example in `book_flight`.
:::

### {doc}`adding-memory`

:::{exercise}
In [Exercise 5.2](adding-memory.md#exercise-52-change-and-forget) you changed `MEMORY.md` to
"Prefers **the most expensive flights**". What happened, and why is this a risk?
:::

:::{solution}
The agent likely recommended the most expensive flight, against the travel policy. `MEMORY.md` is
added to every request, so whoever can edit it steers all future sessions: memory poisoning.
:::

### {doc}`multi-agent`

placeholder

### {doc}`evaluation`

:::{exercise}
The agent answers "What time is it?" correctly. Why look at the trace anyway?
:::

:::{solution}
It may call `get_current_datetime` far more often than needed: right answer, but slower and more
expensive.
:::

### {doc}`security`

placeholder

## Next steps

What are topics that are beyond the scope of this training?

### When do we need an agent?

:::{admonition} Maslow's hammer
:class: tip

{attribution="Abraham H. Maslow"}
> I suppose it is tempting, if the only tool you have is a hammer, to treat everything as if it were
> a nail.

Source: *The Psychology of Science: A Reconnaissance* (1966)
:::

- An agent is flexible, but slower, more expensive and less predictable than plain code.
- If the steps are known in advance, a fixed workflow or a single LLM call is often enough. Example:
  sorting incoming emails into categories needs no loop and no tools.
- An agent pays off when the next step depends on intermediate results. Example: finding a flight
  that fits the travel policy, the user's preferences and the available seats.
- Start with the simplest solution and add autonomy only when it is needed.

### Bias and regulation

- LLMs inherit biases from their training data. An agent that acts on these biases can treat people
  unequally, so keep a human in the loop for decisions that affect people.
- The [EU AI Act](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai) sets
  obligations depending on the risk level of the use case.
- [GDPR](https://commission.europa.eu/law/law-topic/data-protection_en) applies as soon as an agent
  processes personal data, including what ends up in memory files and traces.
- Someone has to be responsible for what the agent does. Tell users that they are dealing with an
  AI, and keep traces so that decisions can be explained afterwards.
- With a hosted provider, prompts, tool results and memory leave your infrastructure. Check how long
  the provider keeps the data and whether it is used for training.

### More complicated MCP servers

- [Authentication and access control](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/index):
  remote MCP servers need to know who is calling them, usually through OAuth. Give each agent only
  the tools and permissions it needs for its task.
- [Elicitation](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation):
  the server can ask the user for missing input during a tool call. Example: `book_flight` could ask
  for the passenger name instead of letting the model make one up.

### Observability, continuous monitoring

- Keep tracing in production, not only during development. Watch task success, errors, number of
  steps and cost per run, and set limits on steps, tokens and time. The
  [OpenTelemetry semantic conventions for generative AI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
  define a common format for these traces.
- Models and providers change over time. Rerun the evaluation dataset after every change, and add
  runs that went wrong in production to the dataset.
- Traces contain prompts, tool results and often personal data, so decide who can see them and how
  long they are kept.

### Licences and lock-in

- Open-weight does not mean [open source](https://opensource.org/ai/open-source-ai-definition).
  Check the model's licence before using it in a product, as some restrict commercial use or require
  their own terms of use.
- Providers change prices and retire models. Keep the model swappable behind an OpenAI-compatible API
  and offer tools through MCP, so that you can move to another provider or your own hardware.

### Other courses and references

- [Responsible Use of Generative AI in Assisted Coding](https://coderefinery.github.io/coding-with-ai/)
  by CodeRefinery, for working with coding agents such as Claude Code and Codex.
- [Infrastructure for AI agents](https://docs.lumi-supercomputer.eu/laif/software/agent-infrastructure/)
  on LUMI: a container for running coding agents more securely, and an MCP server that searches the
  LUMI documentation. See also the
  [AI agent guide](https://docs.lumi-supercomputer.eu/development/ai-tools/ai-agent-guide/).
- Upcoming courses: [LUMI AI Factory trainings](https://lumi-ai-factory.eu/trainings/) and
  [Sweden AI Factory events and workshops](https://swedenaifactory.se/events-and-workshops/).

:::{admonition} Feedback
:class: important

We will share a feedback form at the end of the session. Please take a few minutes to fill it in:
it helps us improve the training.
:::

### Getting support

- The EuroHPC AI Factories help start-ups and SMEs with computing resources, consulting and training,
  much of it free of charge. A good first step is the
  [Playground Access](https://www.eurohpc-ju.europa.eu/playground-access-ai-factories_en) call for
  quick experiments.
- [LUMI AI Factory](https://lumi-ai-factory.eu/service-catalogue/): see also
  [pricing and eligibility](https://lumi-ai-factory.eu/pricing-and-eligibility/).
- [Sweden AI Factory](https://swedenaifactory.se/all-services/)
