# Evaluating an agent

So far we have gradually extended our flight-booking assistant. We started with
a simple chat interface, then added tools, then memory, and finally the ability
to combine multiple tools to solve more realistic tasks.

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

> Book me a flight to Tokyo next Tuesday.

Suppose the final answer looks correct. Was the agent successful? Maybe.

Perhaps it found an appropriate flight immediately, or it called the
flight search tool twenty times, repeated the same searches, ignored user
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

In general, we may be also insterested in knowing how many tokens were
consumed, as well as where most of the execution time was spent. As the system
becomes more capable, evaluation becomes progressively more important.

## Looking inside an agent run

To answer the questions we posed earlier, we need to be able to trace the
behaviour of the agent. This is often called *observability*.

Pydantic AI (or LogFire) includes instrumentation support based on
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
├── datetime_tool
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

The trace may still reveal that the agent called the date tool many more times
than needed, or used significantly more tokens than expected: the final answer
may still be correct, but the implementation is clearly less efficient.

## Traces as evaluation data

Once traces are available, they can become part of the evaluation process; for
example, consider the prompt:

```text
Book me a flight to Berlin next week.
```

A successful evaluation might require:

- at least one call to the datetime tool
- at least one call to the flight search tool
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
  Correct answer using the datetime tool
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
datetime_tool() should be called
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
  Book a flight to Berlin.
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
  expectation: "uses datetime tool"

- prompt: "I prefer window seats"
  expectation: "stores preference"

- prompt: "What is my seating preference?"
  expectation: "retrieves stored preference"

- prompt: "Book me a flight next week"
  expectation: "uses datetime tool and flight search"

- prompt: "Find a flight to Rome"
  expectation: "uses flight search"
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
assert datetime_tool_called
assert memory_retrieved
assert flight_search_called_once
```

These deterministic checks are often reliable and easy to understand.

Other times, however, we want to assess qualities that are hard to judge deterministically: the "friendliness" of a reply, completeness, subjective language quality, and so on. In such situations, developers sometimes use another language model as a judge. The judge receives the user request, the agent response, and possibly the trace, and then evaluates whether the behaviour satisfies certain criteria. The easiest way of doing this is to instantiate another Pydantic agent and feed it the trace, so that it can return a typed result:

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
preferable.

## What should we remember?

When building an agent, evaluation should not be treated as a final step performed after everything else is finished.
A useful evaluation strategy often combines several perspectives:

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
