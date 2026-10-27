# Agentic AI: Beyond Coding Assistants and Chatbots

A hands-on workshop on building AI agents step by step. We build agents in stages, starting with a
plain OpenAI REST API call and ending with multi-agent workflows in [Pydantic AI](https://ai.pydantic.dev/).
The models run on the LUMI supercomputer and are served by the [Aitta](https://aitta.csc.fi/) inference
service. Our running example is a flight-booking assistant.

We cover:

- LLM basics and inference, including serving models with the AITTA inference server and using prompt
  templates
- Building agents from scratch, from a single REST call to structured workflows
- Agent components: model, harness, loop, tools, MCP servers, skills and memory
- Security and evaluation, including running agents reliably outside a laptop

:::{prereq}
- Prior Python programming experience. No machine learning background is needed.
- Basic use of a terminal and a code editor.
- A laptop with Linux, macOS or Windows (WSL recommended on Windows) and [git](https://git-scm.com/).
- A LUMI account, used to log in to Aitta. Course participants are added to a LUMI project for the
  training.
- Optional: Docker, for viewing traces with Jaeger.

Follow the [setup instructions](setup.md) before the workshop.
:::

## Schedule

The workshop runs online over four afternoons in November 2026. Registration and further details are on
the [course page](https://csc.fi/en/training-calendar/agentic-ai-beyond-coding-assistants-and-chatbots/).

:::{important}
The Zoom link and the instructions for getting your LUMI account have been sent to you by email.

We highly encourage you to join the setup session on Monday. We will go through the
[setup](setup.md) together and fix any problems, so that the hands-on exercises run for you from the
first day.
:::

The times of the episodes are approximate and include the exercises.

### Setup session · Monday 2 November: Pre-workshop setup with AITTA and the training environment

🇸🇪 13:00–14:00 (CET) · 🇫🇮 14:00–15:00 (EET)

```{csv-table}
:delim: ;
:widths: auto
:width: 100%
:header: Time; Episode

60 min ; {doc}`setup`
```

### Day 1 · Tuesday 3 November: LLMs and agents with simple tool calling

🇸🇪 12:30–15:30 (CET) · 🇫🇮 13:30–16:30 (EET)

```{csv-table}
:delim: ;
:widths: auto
:width: 100%
:header: Time; Episode

15 min ; Welcome and practicalities
45 min ; {doc}`large-language-model`
10 min ; ☕ Break
60 min ; {doc}`agent-basics`
10 min ; ☕ Break
40 min ; {doc}`mcp`
```

### Day 2 · Wednesday 4 November: Agentic workflows with skills, memory and multiple agents

🇸🇪 12:30–15:30 (CET) · 🇫🇮 13:30–16:30 (EET)

```{csv-table}
:delim: ;
:widths: auto
:width: 100%
:header: Time; Episode

45 min ; {doc}`adding-skills`
10 min ; ☕ Break
45 min ; {doc}`adding-memory`
10 min ; ☕ Break
70 min ; {doc}`multi-agent` (in preparation)
```

### Day 3 · Thursday 5 November: Evaluation, risks and security

🇸🇪 12:30–15:30 (CET) · 🇫🇮 13:30–16:30 (EET)

```{csv-table}
:delim: ;
:widths: auto
:width: 100%
:header: Time; Episode

50 min ; {doc}`evaluation` (in preparation)
10 min ; ☕ Break
80 min ; {doc}`security` (in preparation)
10 min ; ☕ Break
30 min ; {doc}`outlook` (in preparation)
```

## Credits

:::{admonition} How do I get 1 ECTS credit or a certificate?
:class: important

[Aalto Scientific Computing](https://scicomp.aalto.fi/) has kindly offered to give 1 ECTS credit for this workshop.

- Do all the exercises and report your results in a text, PDF, Markdown or Word file. For each exercise,
  include:
  - the prompts you gave the agent and its answers;
  - the relevant part of the agent's log, for example the tool calls and their results. You can copy
    the log from your terminal or add screenshots;
  - your code, if the exercise asks you to write some, for example the `book_flight` tool or your own
    `SKILL.md`;
  - a few sentences answering the questions in the exercise.
- Send everything to <scip@aalto.fi> by 30 November 2026. Ideally, you do all the tasks during the
  course: remember that the LUMI training project, and with it your
  access, ends on 23 November 2026.
- If you are a doctoral student in Finland, add Aalto University's SCI-L1010 to your study program
  (see [doctoralcourses.fi](https://www.doctoralcourses.fi/aalto-courses/)).
- If you are **not** a doctoral student in Finland, you get a certificate to give to your study
  coordinator or supervisor to register it, similar to a workshop at a conference.
:::

```{toctree}
:caption: Setup
:maxdepth: 1
:hidden:

setup.md
```

```{toctree}
:caption: Day 1: LLMs, agents and MCP
:maxdepth: 1
:hidden:

large-language-model.md
agent-basics.md
mcp.md
```

```{toctree}
:caption: Day 2: Skills, memory and multiple agents
:maxdepth: 1
:hidden:

adding-skills.md
adding-memory.md
multi-agent.md
```

```{toctree}
:caption: Day 3: Evaluation and security
:maxdepth: 1
:hidden:

evaluation.md
security.md
outlook.md
```

```{toctree}
:caption: Reference
:maxdepth: 1
:hidden:

quick-reference
guide
```

## Learning outcomes

This workshop is for IT professionals, software engineers and data scientists, for programmers who want
to use AI beyond a chat interface, and for people who use chatbots or coding assistants and want to
understand how they work.

By the end of this workshop, learners should be able to:

- Identify the main components of an AI agent and explain concepts such as tool calling and MCP.
- Build agents in stages and connect tools, MCP servers and memory to them.
- Analyze pitfalls when moving agents from development to production.

## See also

:::{admonition} Credit
:class: warning

This workshop is organized by the LUMI AI Factory Service Center and Sweden AI Factory.

If you are interested in using AI coding assistants responsibly in your research software work, check
out the CodeRefinery lesson
[Responsible Use of Generative AI in Assisted Coding](https://coderefinery.github.io/coding-with-ai/).

:::

::::{admonition} License
:class: attention

:::{admonition} CC BY-SA for media and pedagogical material
:class: attention dropdown

Copyright © {{ copyright }}. This material is released by LUMI AI Factory and Sweden AI Factory under the Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).

**Canonical URL**: <https://creativecommons.org/licenses/by-sa/4.0/>

[See the legal code](https://creativecommons.org/licenses/by-sa/4.0/legalcode.en)

## You are free to

1. **Share** — copy and redistribute the material in any medium or format for any purpose, even commercially.
2. **Adapt** — remix, transform, and build upon the material for any purpose, even commercially.
3. The licensor cannot revoke these freedoms as long as you follow the license terms.

## Under the following terms

1. **Attribution** — You must give [appropriate credit](https://creativecommons.org/licenses/by-sa/4.0/#ref-appropriate-credit) , provide a link to the license, and [indicate if changes were made](https://creativecommons.org/licenses/by-sa/4.0/#ref-indicate-changes) . You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
2. **ShareAlike** — If you remix, transform, or build upon the material, you must distribute your contributions under the [same license](https://creativecommons.org/licenses/by-sa/4.0/#ref-same-license) as the original.
3. **No additional restrictions** — You may not apply legal terms or [technological measures](https://creativecommons.org/licenses/by-sa/4.0/#ref-technological-measures) that legally restrict others from doing anything the license permits.

## Notices

You do not have to comply with the license for elements of the material in the public domain or where your use is permitted by an applicable [exception or limitation](https://creativecommons.org/licenses/by/4.0/deed.en#ref-exception-or-limitation) .

No warranties are given. The license may not give you all of the permissions necessary for your intended use. For example, other rights such as [publicity, privacy, or moral rights](https://creativecommons.org/licenses/by/4.0/deed.en#ref-publicity-privacy-or-moral-rights) may limit how you use the material.

This deed highlights only some of the key features and terms of the actual license. It is not a license and has no legal value. You should carefully review all of the terms and conditions of the actual license before using the licensed material.

:::

:::{admonition} MIT for source code and code snippets
:class: attention dropdown

MIT License

Copyright (c) {{ copyright }}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

:::

::::
