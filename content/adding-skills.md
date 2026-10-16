# 4. Skills

:::{questions}
- What is a skill, and what problem does it solve?
- How does an agent decide when to load a skill?
- How do skills differ from system prompts and MCP tools?
:::

:::{objectives}
- Understand the structure of a `SKILL.md` file.
- Understand which parts of a skill end up in the LLM's context, and when.
- Add a skill to the agent and write your own.
:::

## Why skills?

In the previous lessons we have covered tools and made them available via an MCP server. Our agent can
now look up the date, search for flights, and book them with the `book_flight` tool from Exercise 3.2. However, as the MCP tools are general, they
are not customized to how we want to use the tools. For example, company rules, conventions, and workflows 
are not included in the context of the LLM when interacting with it. There are multiple options for including
these instructions in the context:

1. Include everything in the system prompt of our harness but then the context will grow with every customization
even if it is not relevant for the current interaction. For example, detailed train preferences are not relevant
when searching flights.

2. Another option is to write a new tool. But that is overkill for something that just includes natural language
and everyone should be able to modify even when they do not have any coding experience.

Skills are a compromise between both: They are packaged instructions in natural language files, of which only
the name and description are always loaded, while the full instructions are included only when they are needed.

Keeping the context small matters. LLMs are stateless, so the whole context is sent again with every
request, including every round trip for a tool call. A larger context takes longer to process before the
first token is generated, and with providers that bill per token, every extra token in the system prompt
is paid for again on each request. Prompt caching can reduce this cost for a context that stays the same.
Very long contexts can also make the model worse at picking out the instructions that matter.

## Structure of a skill
A skill is a folder containing a `SKILL.md` file (plus optional scripts, references, assets). Skills follow
an [open standard](https://github.com/agentskills/agentskills) and are supported by several harnesses 
(coding agents, frameworks), which makes them portable in a similar way as the MCP server in the earlier
example.

Let's look at a concrete example: For our running example of a flight booking agent, we could imagine
that our company has some travel policy that we need to follow. While the MCP server could be provided
by the travel agency, the skills are custom to our company. Let us explore the travel-policy skill.

The folder layout in our example is as follows:

```text
agent-skills/
└── travel-policy/
    └── SKILL.md
```

Where the `SKILL.md` file consists of a YAML frontmatter and some markdown body. The frontmatter
includes the `name` and `description` fields that are standardized. The `name` and `description` are
what is included in the context of the LLM to select different skills from all available skills
if they seem likely to be relevant. This is comparable to the tool docstring in the previous
lesson. The markdown body includes natural language. See the `travel-policy/SKILL.md`:

```{literalinclude} hands-on/agent-skills/travel-policy/SKILL.md
:language: markdown
```

:::{instructor-note}
Highlight rule 5: Skills can also tell the agent to ask the user something.
:::

## How skills work
As described earlier, skills work following the _progressive disclosure_ idea: At first only the 
name and description are loaded into the context, then later the whole skill. You can compare this using
the tabs. The [Agent Skills specification](https://agentskills.io/specification#progressive-disclosure) describes progressive disclosure in more detail.

::::{tabs}
:::{group-tab} At startup
Only the frontmatter of every skill is added to the context:

```{literalinclude} hands-on/agent-skills/travel-policy/SKILL.md
:language: yaml
:lines: 2-3
```
:::

:::{group-tab} When the skill is loaded
The full body is added to the context:

```{literalinclude} hands-on/agent-skills/travel-policy/SKILL.md
:language: markdown
:lines: 6-
```
:::
::::

The main steps are as follows. You can compare them with the MCP log walk-through in Exercise 3.1:
  1. Harness scans the skills folder and extracts the name and descriptions.
  2. Name and description are appended into the context, together with a tool to load a skill (`load_capability`).
  3. The LLM detects that a skill is relevant and generates a tool call to `load_capability`. The inference server parses it into a structured tool call.
  4. The harness executes `load_capability` and returns the skill body as tool result.
  5. The skill body is added to the context of the LLM, and LLM (hopefully) follows the instructions.

Because of the progressive disclosure, many skills can be available while costing only a few tokens each.

:::{discussion}
Why does the `description` matter so much? What would happen with a description like "Some rules"?
:::

## Adding skills to the agent

How do we include the skills into the framework? Skills are another capability besides our MCP server.
We first give the harness file access, rooted at the script's directory using `LocalWorkspace` and 
add the skill using `Skills("./agent-skills", include=[...])`. We can see that the MCP server from the 
previous lesson is still attached. Through the `instructions` block we nudge the model to load relevant
skills before answering.

For the model, the `instructions` are the system prompt: Pydantic AI sends them as a `system` message
at the start of every request. Pydantic AI also has a separate `system_prompt` argument. The difference
only matters for the conversation history: a `system_prompt` is stored in the message history and re-sent
from there, while the `instructions` are always taken from the current agent. The `Skills` capability uses
the same mechanism: the list of skill names and descriptions is added to the instructions.

```{literalinclude} hands-on/05_skills.py
:start-at: agent = Agent(
:end-before: async def main():
:emphasize-lines: 10-11
```

## Exercise 4.1: Try out the skill
Try out the skill. The agent uses the tools from the MCP server, so we first need to start it. In this
lesson we use the model solution of Exercise 3.2, which also has the `book_flight` tool. If an MCP server
from the previous lesson is still running, stop it first. Then start the model solution MCP server in a
separate terminal from the `hands-on` directory:

```bash
uv run mcp run 04_mcp_server_solution.py --transport streamable-http
```

Run the agent with the skill with the following command.

```bash
uv run 05_skills.py
```

There are multiple prompts you could try. For example, start with:

```text
Are there any flights from Paris to Rome tomorrow?
```

Once the agent has answered, follow up with:

```text
Does it comply with the travel policy?
```

Observe in the log of your agent. Is `load_capability` called? Before or after `search_flights`?

If the skill is not loaded automatically, you can nudge the agent by naming the skill in your prompt.
Note that `/travel-policy` is not a special command in our harness, unlike the slash commands in many
coding agents. It is ordinary text that matches the skill name in the list of available skills, which
makes the model more likely to call `load_capability`.

```text
/travel-policy
```

Does the agent ask whether you prefer morning or afternoon flights, as rule 5 of the skill demands?

Next, look at what the model actually received. Find the `load_capability` call and its tool result in
the log. The skill body comes back as an ordinary tool result, just like the MCP tool results in
Exercise 3.1.

Finally, check the agent's recommendation by hand against `data/flights.csv`, which contains the columns
`price_eur`, `distance_km` and `aircraft_type`. Is the cost per km really at most 0.25 EUR? Is a wide
aircraft used on a flight below 1000 km? Did the agent get the arithmetic right? The Paris–Rome flights
all comply, so also try a route where some flights violate the policy:

```text
I want to fly from Munich to Zurich next Tuesday afternoon.
```

<details>
<summary>Solution: Compare with what you saw</summary>

A typical run calls `load_capability` with `{"id": "travel-policy"}`, `get_current_datetime` to resolve
"tomorrow", and `search_flights`. The order of `load_capability` relative to the other tools can differ.
If the skill is loaded before `search_flights`, the agent may first ask whether you prefer morning or
afternoon flights. The tool result of `load_capability` contains the body of `SKILL.md`.

Whether and when the skill is loaded depends on the model and on how well the `description` matches your
prompt. The same prompt can load the skill in one run and skip it in the next. If the skill is not loaded,
the agent will answer without applying the policy.

The Paris–Rome flights cost between 0.10 and 0.13 EUR/km and none uses a wide aircraft, so all of them
comply. For Munich–Zurich (242 km) on a Tuesday, there are only two flights: LH199 at 06:45 (58 EUR,
0.24 EUR/km) complies, but LH200 at 11:45 (71 EUR, 0.29 EUR/km) exceeds the limit. There is no afternoon
flight on Tuesdays. The agent should say so, not recommend LH200 without pointing out the violation, and
suggest LH199 as the compliant alternative. Since your prompt already says "afternoon", the agent should
not ask for your preference again (rule 5). Check whether your agent did this and whether its numbers are
correct.

</details>

## Exercise 4.2: Write your own skill
Let us now write our own skill. It should be a skill that tells the agent to always confirm before booking a flight.

The MCP server that you started in Exercise 4.1 already has the `book_flight` tool.

The folder for the new skill already exists: `agent-skills/booking-confirmation/`. Create a `SKILL.md`
in it and use `booking-confirmation` as the `name` in the frontmatter, since the name must match the
folder name. Then add the skill to `include=[...]` in `05_skills.py` and restart the agent.

Try out the skill, e.g., by trying to book a flight. Is it working as you intended?

<details>
<summary>Example solution</summary>

Create `agent-skills/booking-confirmation/SKILL.md`:

```markdown
---
name: booking-confirmation
description: Rules to follow before booking a flight with the book_flight tool. Use whenever the user asks to book, reserve or buy a flight.
---

# Booking confirmation

Before calling `book_flight`:

1. Summarize the booking: flight number, origin, destination, date, departure time, price and passenger name.
2. Ask the user to explicitly confirm the booking.
3. Only call `book_flight` after the user has confirmed in their latest message. If they decline or change details, do not book.
4. If the passenger name is missing, ask for it. Never make one up.
```

Then include it next to the travel policy in `05_skills.py`:

```python
Skills("./agent-skills", include=["travel-policy", "booking-confirmation"]),
```

</details>

## Skills compared to related ideas

Let us briefly recap and discuss how skills compare to related ideas like system prompts and MCP tools.

| | System prompt (our `instructions`) | MCP tool | Skill |
|---|---|---|---|
| What it is | Instructions set in the harness, in our agent the `instructions` sentence plus the list of skill names and descriptions | A function that the MCP server executes when the LLM requests it | Instructions in a `SKILL.md` file, optionally with bundled files |
| When in context | Always, with every request | Definition (name, docstring, parameters) always, result from the call onwards | Name and description always, body from loading onwards |
| Who decides to use it | Nobody, it always applies | The LLM, by requesting a tool call | The LLM, by calling `load_capability` |
| Can execute code | No | Yes | The standard allows [bundled scripts](https://agentskills.io/specification#scripts/), but the `Skills` capability we use never runs them |
| Who writes it | Whoever builds the harness: here us, in `05_skills.py` | The MCP server provider, e.g. the travel agency | Anyone, no coding needed |
| Reusable across harnesses | Only by copying the text | Yes, via any MCP client | Yes, in any harness that supports the standard |

Skills and tools complement each other: tools define *what the agent can do*, skills describe *how it
should do it*.

Skills are suggestions, not enforcement. A rule like "Cost per km must not exceed 0.25 EUR" is only text
in the context, and the LLM can ignore it or miscalculate, as you may have seen in Exercise 4.1. Hard
rules belong in code, for example in a tool that rejects bookings that violate the policy. Skills are
better suited for guidance, conventions and workflows. How to check whether an agent actually follows
the rules is covered in the [evaluation section](evaluation.md).

Finally, skills are instructions that go straight into the context of the LLM, so only use skills you
trust. More on this in the [security section](security.md).

:::{discussion}
What would be skills that you could imagine?
:::

:::{instructor-note}
Discuss <https://github.com/CSCfi/csc-skills>
:::

## Summary

A skill is a folder containing a `SKILL.md` file, which consists of a YAML frontmatter with `name` and
`description` and a markdown body with instructions in natural language. Skills follow an open standard,
so the same skill can be used in different harnesses.

Skills follow the idea of progressive disclosure: the name and description of every skill are always in
the context, while the body is only loaded when the LLM decides that the skill is relevant, by calling
the `load_capability` tool. This keeps the context small even with many skills available, but it also
means that a skill with a vague description may never be loaded.

In Pydantic AI, we added skills with the `Skills(...)` capability, next to the MCP server from the
previous lesson. Skills complement tools and MCP and keep the system prompt small. However, skills only
guide the agent and do not enforce rules: hard constraints belong in code.

Rule 5 of our travel policy relies on the time-of-day preference being known from the conversation
history. What happens when you restart the agent? The preference is gone and the agent asks again. In the
next lesson, we will look at how to give the agent [memory](adding-memory.md).
