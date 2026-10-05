# 1. Large Language Models

:::{questions}
- What is a large language model and how does it generate text?
- Why is an LLM's output variable, and why can it be confidently wrong?
- Why do training cut-off dates matter in practice?
- How do you call an LLM from Python?
:::

:::{objectives}
- Explain next-token prediction and the role of tokens.
- Distinguish pre-training from fine-tuning and instruction tuning, and understand why training cut-off dates matter.
- Call an LLM through the AITTA inference service with the OpenAI client and stream a response.
:::

A Large Language Model (LLM) is a type of artificial intelligence trained on
vast amounts of text data to predict and generate human-like text. 

```{figure} img/llm.png
:alt: general concept of an LLM
:width: 100%
```

<!--
:::{admonition} A more accurate mental model
:class: tip, dropdown
-->

At their core, these models learn statistical patterns in language: given a
sequence of words (or better *tokens*: fragments of words, commas, and anything
in text), they predict what comes next. In order to do so, text must first be
converted into numerical representations, then transformer layers update those
representations using the surrounding context, and finally they are converted
back to text.

```text
text
  -> tokens
  -> token IDs
  -> embeddings
  -> transformer blocks
  -> output logits
  -> next-token probabilities
  -> tokens
  -> text
```

```{figure} img/llm_blocks.png
:alt: Input tokens ->  Model -> Input tokens + output token
:width: 100%

A simplistic mental model for an LLM performing probabilistic next token prediction.
Source: [Simo Tuomisto](https://simo-tuomisto.github.io/understanding-ai-landscape-lecture/#3)
```

LLMs work because language (whether natural language or code) follows consistent
patterns. The model doesn't "understand" text the way humans do, but it has
learned enough patterns to generate coherent and often meaningful output. This
is especially effective for code, which is highly structured, so the model can
generate syntactically correct and often semantically meaningful code.

:::{callout} Key insight
LLMs are sophisticated pattern-matching systems that can perform multi-step reasoning, but their reasoning is fallible and outputs must be verified. They
excel at common patterns but can confidently produce incorrect output for novel
or complex problems. **Always verify their output**.
:::

:::{admonition} Stochastic parrots
:class: tip

{attribution="Emily M. Bender and Timnit Gebru"}
>  LM \[Language Model\] is a system for haphazardly stitching together sequences of linguistic forms it has observed in its vast training data, according to probabilistic information about how they combine, but without any reference to meaning: a stochastic parrot.

Source: <https://doi.org/10.1145/3442188.3445922>
:::

:::{admonition} Practitioner's perspective: Simon Willison
:class: tip


{attribution="Simon Willison"}
> My current favorite mental model is to think of them as an over-confident
pair programming assistant who's lightning fast at looking things up, can
churn out relevant examples at a moment's notice and can execute on tedious
tasks without complaint.
>
> **Over-confident** is important. They'll absolutely make mistakes, sometimes
subtle, sometimes huge. These mistakes can be deeply inhuman, if a human
collaborator hallucinated a non-existent library or method you would
instantly lose trust in them.
>
> **Don't fall into the trap of anthropomorphizing LLMs and assuming that
failures which would discredit a human should discredit the machine in the
same way.**"

Source: ["How I use LLMs to help me write code"](https://simonwillison.net/2025/Mar/11/using-llms-for-code/)
:::


## How are LLMs trained?

Training an LLM involves two main phases:

### 1. Pre-training

The model is exposed to massive amounts of text (and often code)
to learn general patterns of language:

| Model | Training Data Size | Languages |
|-------|-------------------|-----------|
| Poro 34B | ~1 trillion tokens | Finnish, English, code |
| Gemma | Undisclosed (Gemma 2: ~13 trillion tokens) | Multilingual + code |
| GPT-OSS | Undisclosed | Multilingual + code |
| GPT-5.x | Undisclosed | Multilingual + code |


During pre-training, the model learns:
- Grammar and structure of natural language (and the syntax of programming languages)
- Common patterns, idioms, and factual associations
- Relationships between concepts across a document
- How different parts of a text (or codebase) relate to each other

The size of typical datasets also implies that training a model from scratch
is a heavy commitment. It is expensive, both in terms of time (person-hours) and
compute, which in turn means that very few actors do this and most users rely on
such pre-trained "frontier" models for their specific use cases.

In our course we use the AITTA inference service that serves such frontier models via an API. We just need to implement the API client and then can use such models in our Python code.


### 2. Fine-tuning and instruction tuning

After pre-training, models are often further refined:

- **Fine-tuning**: Training on specific domains (e.g., scientific Python)
- **Instruction tuning**: Teaching the model to follow human instructions
- **RLHF** (Reinforcement Learning from Human Feedback): Aligning outputs with human preferences

In our exercise we use an instruction-tuned model that lets us send a prompt as a message with a role (`messages=[{"role": "user", "content": prompt}]`) and get a helpful response.

## Training cut-off dates matter

A crucial characteristic of any model is its **training cut-off date**, the
date at which training data collection stopped. This has direct practical
implications, which are especially visible in coding:

| Impact | Example |
|--------|---------|
| Unknown libraries | A library released after the cut-off won't be suggested |
| Breaking changes | Major API changes since cut-off produce outdated suggestions |
| Deprecated patterns | Old syntax or methods may still be recommended |
| Security updates | Known vulnerabilities patched after cut-off won't be reflected |

:::{callout} Key insight
The training cut-off date is sometimes not known. With chatbots, you can try asking the chatbot.
What makes it even more challenging is that some **AI systems also have *"tools"*** attached to them,
so they can fetch **some** up-to-date content, while mixing with what they have seen during
their training. This can be a total success... or total disaster. 

Pick a stable library, even if it is a little bit older: [Choose Boring Technology](https://boringtechnology.club/).
:::


**Practical implications:**
- Check model documentation for training cut-off dates
- Be skeptical of suggestions for rapidly-evolving libraries 
- Provide recent documentation or examples in prompts when using newer tools
- Consider library stability as a factor in dependencies choices

## Exercise 1.1: Use an LLM

To use an LLM in our code, we need to create a client.
Even though the LLM provider in our case is [AITTA](https://aitta.csc.fi), an inference service that runs LLMs on the LUMI supercomputer, we use the [OpenAI Python library](https://pypi.org/project/openai/).
AITTA implements a subset of the [OpenAI API](https://github.com/openai/openai-openapi), which has become a de facto standard for LLM APIs. This means we can easily switch to any other provider that implements the same API.

We use `AsyncOpenAI`, the asynchronous version of the client, which works with [`asyncio`](https://docs.python.org/3/library/asyncio.html). `asyncio` is Python's built-in library for running many tasks concurrently in a single program, so that while one task waits (for example, for an LLM to respond), others can keep working instead of sitting idle. This lets us send multiple requests to the LLM at the same time instead of one after another. We don't need this yet, but it will be useful in later exercises.

The `base_url` is set here to use AITTA, but it can be changed. For example, you can set it to `http://localhost:8000/v1` when running vLLM locally, or to `https://api.openai.com/v1` for OpenAI.

The API key authenticates you to the service. Keep it secret and never share it with anyone. See the [setup section](./setup.md) for how to obtain one for AITTA.


```{literalinclude} hands-on/01_hello_world.py
:end-before: async function
```

Now we can use our client to send the prompt `"Where does 'hello world' come from?"` to the model `LumiOpen/Poro-34B-chat`.

Setting `stream=True` tells the API to send the response in small pieces, called tokens, as soon as the model produces them, rather than waiting until the whole answer is finished.

We receive these pieces one at a time in the `async for` loop. Each `event` contains a `delta` with only the text that is new since the previous event. Printing with `end=""` joins the pieces into continuous text, and `flush=True` makes each one appear on screen immediately instead of being buffered.

```{literalinclude} hands-on/01_hello_world.py
:start-after: async function
:end-before: if __name__ == "__main__":
```

You can run it yourself with the following command. Make sure you have set up your API key correctly as described in the [setup section](setup.md).

```shell
uv run 01_hello_world.py
```

You should receive a reply to your prompt, but note that the exact reply can change because LLMs are stochastic. Here is an example that we got.

```text
The tradition of writing a "Hello, World!" program is widely attributed to **Brian Kernighan**, a computer scientist at Bell Labs.

While many people associate it with the C programming language, its origin happened in two stages...
```

Try changing the prompt by passing a new prompt to the script with:

```shell
uv run 01_hello_world.py "Where does the name Python come from?"
```

This is a bit clumsy, so in the next part we will make it interactive, letting you type new prompts directly from the command line without needing to restart the script.

## Summary

A large language model predicts text one token at a time. Text is split into
tokens, converted into numerical representations, passed through transformer
blocks that use the surrounding context, and turned back into probabilities for
the next token. Because this process is probabilistic, the output is stochastic
and pattern-based: it can be wrong even when it looks confident, so you should
always verify what the model produces.

Models are built in two phases. Pre-training exposes the model to large amounts
of text (and code) so it learns general patterns, and fine-tuning and
instruction tuning then teach it to follow human instructions. Training always
stops at a cut-off date, so a model may not know about newer libraries or recent
changes.

In Exercise 1.1 we used such a model in practice. We created an `AsyncOpenAI`
client pointed at the AITTA inference service, sent a prompt to
`LumiOpen/Poro-34B-chat`, and streamed the reply token by token. Because the
output is stochastic, the exact reply changes each time you run it.