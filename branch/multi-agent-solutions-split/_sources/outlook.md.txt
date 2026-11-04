# 9. Outlook

In this last section we first recap the workshop with three short questions. Then we look at topics
beyond the scope of this training and at how to continue after the workshop.

## Recap: which method would you use?

Try to answer before opening the solutions. The {doc}`quick-reference` lists all the terms.

:::{exercise} Enforcing the travel policy
The flight-booking agent must never book a flight that costs more than 500 EUR. What do you use?

- **A**: A skill with the rule
- **B**: A note in `MEMORY.md`
- **C**: A check in the `book_flight` tool
- **D**: A sentence in the instructions of the agent
:::

:::{solution}
**C**: skills, memory and instructions only guide the LLM, which can ignore them or miscalculate.
Only code enforces the limit. See {doc}`adding-skills`.
:::

:::{exercise} Choosing the method
Which method fits each task best? Pick one of the four options for each task.

1. Filter and compute over terabytes of data that have no API to query them
2. Follow soft guidelines, such as the style of a booking confirmation
3. Interact with the local environment, for example by running some commands
4. Run a long workflow with strict steps

- **A**: Skills
- **B**: A multi-agent workflow with programmatic hand-off
- **C**: Tools
- **D**: A remote MCP server that runs next to the data
:::

:::{solution}
1. **D**: the MCP server runs where the data is and returns only the results, so the data does not
   have to move. See {doc}`mcp`.
2. **A**: skills guide the agent but do not enforce rules. See {doc}`adding-skills`.
3. **C**: tools run on the machine of the harness. A local MCP server works too. See
   {doc}`agent-basics`.
4. **B**: code calls the agents in a fixed order and validates the output of each step. See
   {doc}`multi-agent`.
:::

:::{exercise} Reading partner websites
The agent will read flight offers from partner websites. How do you protect it?

- **A**: Trust the content, because the partners are known
- **B**: Add a skill that tells the agent to ignore instructions on websites
- **C**: Treat the content as untrusted, filter the output for unexpected URLs and credential
  requests, and test the agent with injected content
- **D**: Store the offers in `MEMORY.md` first
:::

:::{solution}
**C**: website content can contain indirect prompt injection, like the poisoned row in
[Exercise 8.1](security.md#exercise-81-prompt-injection). A skill alone does not enforce anything,
and memory would make the injected text affect all future sessions. See {doc}`security`.
:::

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

### Serving your own models

The examples use Aitta, but they work with any server that offers an OpenAI-compatible API. Set
`MODEL_BASE_URL`, `MODEL_NAME` and `OPENAI_API_KEY` in `.env` to point them to another server.

- On a supercomputer, you can serve models yourself, for example with
  [vLLM](https://github.com/Lumi-supercomputer/LUMI-AI-Guide/tree/main/10-LLM-inference) or with
  [llama.cpp](https://swedenaifactory.se/short-tutorials/2026/03/using-an-llm-on-a-supercomputer/).
  A supercomputer is meant for research and development, not for production: jobs wait in a queue
  and maintenance stops all services. Use it to develop and evaluate your agent, and run the
  production service elsewhere. See the LUMI AI Factory guide on the
  [road to production](https://lumi-ai-factory.eu/user-support/road-to-production/).
- Your institution may also host LLMs. Any service that gives API access to the models should
  work. See the [models that Pydantic AI supports](https://pydantic.dev/docs/ai/models/overview/).

### More multi-agent patterns

- We covered programmatic hand-off and agent delegation. For the most complex cases,
  [graphs](https://pydantic.dev/docs/ai/graph/graph/) control the flow between agents as a state
  machine, and deep agents add [planning](https://pydantic.dev/docs/ai/harness/planning/), file
  operations and sandboxed code execution.
- Each extra agent adds model calls and places to fail. Try a single agent or a fixed hand-off
  first.

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
