# 7. Evaluating an agent

So far we have gradually extended our flight-booking assistant. We started with
a simple chat interface, then added tools, moved them to an MCP server, taught
the agent a travel policy through skills, gave it memory, and finally split the
work across multiple agents.

At this point it is natural to ask a new question:

*How do we know whether the agent is actually getting better?*

This is the purpose of evaluation.

Evaluation is often overlooked when building AI applications. It is fun to add
new features and see the agent perform increasingly complex tasks, but without
evaluation it becomes difficult to know whether a change improved the agent,
made it slower, increased its cost, or introduced new mistakes.

In this episode we will look at a few simple ways to evaluate our agent as it
evolves.

## Evaluating agents is different from evaluating chatbots

A traditional chatbot receives a prompt and produces a response. Evaluating
such a system can often focus on the quality of the final answer.

Agents are different because they can perform actions before responding. They
may call tools, retrieve information from memory, or combine multiple sources
of information before generating a final answer. Consider the request:

> Book me a flight to Helsinki next Tuesday.

Suppose the final answer looks correct. Was the agent successful? Maybe.

Perhaps it found an appropriate flight immediately, or it called
`search_flights` twenty times, repeated the same searches, ignored user
preferences, and produced the right answer only by accident.

For agents, we are often interested in a larger set of metrics, such as:

- the quality of the final result;
- the sequence of decisions used to reach that result;
- the overall cost.

This makes evaluation more interesting, but also more challenging.

## Evaluation follows the capabilities of the agent

As we add new capabilities, new evaluation questions appear: the dimensions
across which we define a "good behaviour" grow with the number of actions the
agent can perform.

When our application was only a chatbot, we could ask:

- Did it answer the question?
- Was the answer understandable?

After adding a date and time tool, we can ask additional questions:

- Did the agent use the tool when necessary?
- Did it correctly interpret phrases such as "tomorrow" or "next Friday"?
- Did it avoid unnecessary tool calls?

After adding memory, we can ask:

- Did the agent remember a previously stored preference?
- Did it retrieve the correct preference?
- Did it invent information that was never stored?

After adding multiple tools, we can ask:

- Did the agent choose the correct tool?
- Did it combine information from several tools correctly?
- Did it avoid repeating the same expensive operation?

In general, we may also be interested in knowing how many tokens were
consumed, as well as where most of the execution time was spent. As the system
becomes more capable, evaluation becomes progressively more important.

## Looking inside an agent run

To answer the questions we posed earlier, we need to be able to trace the
behaviour of the agent. This is often called *observability*.

Pydantic AI (or Logfire) includes instrumentation support based on
OpenTelemetry. You may have noticed the following statements in our example
scripts:

```python
logfire.configure(send_to_logfire=False)
logfire.instrument_pydantic_ai()
```

When enabled, each run can be recorded as a trace containing the sequence of
model calls and tool invocations performed by the agent. These logs can then be
examined during evaluation.

A simplified trace might look like:

```text
agent run
├── model request
├── get_current_datetime
├── model request
├── search_flights
├── model request
└── final response
```

Instead of inspecting only the final answer, we can inspect the entire process that produced it.

### Why traces are useful

Traces help us answer questions that are difficult to answer by looking only at the final response.

For example:

```text
User:
  Book me a flight to Rome tomorrow
```

Suppose the answer is correct.

The trace may still reveal that the agent called `get_current_datetime` many more times
than needed, or used significantly more tokens than expected: the final answer
may still be correct, but the implementation is clearly less efficient.

## Traces as evaluation data

Once traces are available, they can become part of the evaluation process; for
example, consider the prompt:

```text
Book me a flight to Paris next week.
```

A successful evaluation might require:

- at least one call to `get_current_datetime`
- at least one call to `search_flights`
- no repeated flight searches with identical parameters

Compared to chatbots, we are also looking at the inner workings of the agent rather than the outcome.

## Simple metrics

Evaluation does not have to start with complicated benchmarks: for a project
such as our flight-booking assistant, a few simple metrics already provide
useful information.

### Task success

Did the agent accomplish the intended task?

For example:

```text
User:
  What day is tomorrow?

Expected:
  Correct answer using get_current_datetime
```

A simple success or failure label is often enough.

### Tool usage

Did the agent call the appropriate tool?

For example:

```text
User:
  What day is tomorrow?
```

Expected:

```text
get_current_datetime should be called
```

Whereas for:

```text
User:
  What is 2 + 2?
```

we would expect no datetime lookup at all.

### Memory usage

Did the agent use stored information correctly?

For example:

```text
User:
  I prefer window seats.
```

followed later by:

```text
User:
  Book a flight to Paris.
```

We would expect the preference to influence the recommendation.

### Cost

Many agent systems are billed according to token usage. While two agents may
produce equally good answers, they might have very different costs.

## Building a small evaluation dataset

In order to assess the performance of the agent, an *evaluation dataset* can (should) be used. This is a collection of example tasks that the agent is supposed to perform, with a known outcome, that we can use to evaluate if the agent improved, was not affected or worsened with a certain change (e.g. a new tool). In a lot of ways, this is similar to regression testing in traditional software development.

For example:

```text
- prompt: "What day is tomorrow?"
  expectation: "calls get_current_datetime"

- prompt: "I prefer window seats"
  expectation: "stores preference"

- prompt: "What is my seating preference?"
  expectation: "retrieves stored preference"

- prompt: "Book me a flight next week"
  expectation: "calls get_current_datetime and search_flights"

- prompt: "Find a flight to Rome"
  expectation: "calls search_flights"
```

Each time we modify the agent, we can run the same set of tests again and compare the results.

### Manual evaluation and automatic evaluation

The simplest evaluation method is to inspect the outputs manually.

This works well when developing the system and experimenting with new features,
but can quickly become unmanageable when we start tracking many different
experiments. Thus, we may find ourselves very quickly wanting to move to
automated checks.

Some checks can be expressed as straightforward rules:

```python
assert get_current_datetime_called
assert memory_retrieved
assert search_flights_called_once
```

These deterministic checks are often reliable and easy to understand, and can
be somewhat extended to "less objective" qualities, such as the quality of a
summary, when a reference answer exists. Common metrics include:

- Exact match between an answer and a reference
- BLEU, which counts how many short-word sequences in the output also appear in
the reference
- ROUGE, which measures how much of the reference is covered by the output.

In such situations, developers sometimes can also use another language model as
a judge. The judge receives the user request, the agent response, and possibly
the trace, and then evaluates whether the behaviour satisfies certain criteria.
The easiest way of doing this is to instantiate another Pydantic agent and feed
it the trace, so that it can return a typed result (bool, a numerical score, or
a label for categorical classification):

```python
from pydantic import BaseModel
from pydantic_ai import Agent


class Evaluation(BaseModel):
    passed: bool
    explanation: str


judge = Agent(
    output_type=Evaluation
)

result = judge.run_sync("""
Did this response satisfy the user's request?

User:
Book me a flight to Paris next week

Response:
I found three flights departing on Tuesday.

Evaluate it.
""")

print(result.output)

```

This can be useful, but it should not replace simpler checks when those are
available. If a fact can be checked directly, a direct check is usually
preferable. More information can be found in the Pydantic
[evals](https://pydantic.dev/docs/ai/evals/evaluators/overview/#_top)
documentation for agentic workflows, and in a Sweden AI Factory
[lesson](https://learn.swedenaifactory.se/roadshow/evaluating-llms/#evaluating-large-language-models)
for LLMs in particular.

## Exercises

::::{exercise} Evaluate the tool calling in our flight booker

We want to deterministically check whether the agent calls the right tools in
the right order. To do it, we will use `pydantic_evals`, which lets us test the
*trajectory* of a agent turn (i.e. if the right tools are called, in the right
order, for the right amount of times). To do this, you can inspect and run the
code in `hands-on/07_eval.py`. The script creates the agent with skills and MCP
like in the previous hands-on, then wires them up for evaluation. The new
snippet is reported here for clarity:

```{literalinclude} hands-on/07_eval.py
:lines: 54-
:language: python
```

As you can see, we create a `Case` which contains the prompt and a few
`evaluators`:

- A `TrajectoryMatch`, i.e. the sequence of tool calls
- An `ArgumentCorrectness` to check whether the tools are called with the right
arguments
- `MaxToolCalls` to check if the total number of tool calls is what we expect.

Then we collect this one-item list of cases into a `Dataset` and we run our
agent on it.

To run this, we will need our MCP server running (`uv run 03_mcp_server.py`).
Try to run the code yourselves and see if the agent behaves according to our
expectations!

::::

::::{exercise} More evaluation!

Let us try to break on purpose the agentic workflow, by trying to prompt the
LLM in a way that it skips a tool call or calls a tool with the wrong
arguments. This exercise is open ended for you to experiment, but a hint is
proposed below.

:::{hint}
:class: dropdown
If we try to create a case where we tell the LLM the current date, it'll
probably skip the datetime tool call.
:::

:::{solution}

The full solution is available at `hands-on/07_eval_solution.py`, but the new
`Case` is reported here for clarity.

```{literalinclude} hands-on/07_eval_solution.py
:lines: 79-98
:language: python 
```

The message of this example is that evaluation is hard, no less because it can
be brittle: while the agent is behaving "correctly", it is still not following
the trajectory we thought it would. Non-determinism is a both the greatest
feature and the most unmanageable part of LLMs.

:::

::::

## Summary

When building an agent, evaluation should not be treated as a final step
performed after everything else is finished. A useful evaluation strategy often
combines several perspectives:

- task success
- correct tool usage
- correct memory usage
- cost
- trace inspection

Once evaluations are in place, improvements become measurable. Instead of
asking whether a new version "feels better", we can compare it against previous
versions and determine whether it actually performs better on representative
tasks.

In that sense, evaluation plays the same role for agents that testing plays for
traditional software: it gives us confidence that the system behaves as
expected when it changes.
