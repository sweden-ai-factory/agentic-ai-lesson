# What is a Large Language Model?

A Large Language Model (LLM) is a type of artificial intelligence trained on
vast amounts of text data to predict and generate human-like text. At their
core, these models learn statistical patterns in language: given a sequence of
words (or better *tokens*: fragments of words, commas, and anything in text), 
they predict what comes next.

```{figure} img/llm.png
:alt: Input tokens ->  Model -> Input tokens + output token
:width: 100%

A simple illustration of an LLM.
```

:::{admonition} Stochastic Parrots
:class: note

{attribution="Emily M. Bender and Timnit Gebru"}
>  LM [Language Model] is a system for haphazardly stitching together sequences of linguistic forms it has observed in its vast training data, according to probabilistic information about how they combine, but without any reference to meaning: a stochastic parrot.

From: <https://doi.org/10.1145/3442188.3445922>
:::


## Anatomy of a Large Language Model

A language model does not read text as words and sentences: text must first be
converted into numerical representations, then transformer layers update
those representations using the surrounding context.

A simplified forward pass looks like this:

```text
text
  -> tokens
  -> token IDs
  -> embeddings
  -> transformer blocks
  -> output logits
  -> next-token probabilities
```

For a generative language model, the process is repeated one generated token
at a time.


### From text to tokens

The first step is tokenisation. A tokeniser divides the input into units
called **tokens** and maps every token to an integer ID.

Tokens do not necessarily correspond to words. Depending on the tokeniser, a
token may represent a complete word, part of a word, punctuation, whitespace,
or another frequently occurring character sequence.

### From token IDs to embeddings

A token ID is an integer label. The numerical distance between two token IDs
has no semantic meaning. Token ID 100 is not inherently more similar to token
ID 101 than it is to token ID 9000.

Before the transformer can process the tokens, the model maps every token ID
to a vector. This operation is performed by an embedding layer.

If the vocabulary contains \(V\) tokens and the model uses an embedding
dimension \(d\), the embedding layer can be represented as a matrix:

```{math}
E \in \mathbb{R}^{V \times d}
```

Looking up a token ID selects the corresponding row of this matrix.

```text
token ID
   |
   v
embedding matrix lookup
   |
   v
vector of length d
```

The embedding matrix is learned during training. Tokens that are useful in
similar contexts often acquire related representations. The number `d` determines
the number of dimensions in the embedding space, and since it is often large, it
can be hard to visualize. We can however project the vectors into a 2D or 3D and
draw some conclusions.


#### Initial and contextual representations

The embedding-layer output is only the initial representation of a token. It
does not yet express what the token means in a particular sentence.

Consider the word `mole`:

::::{figure} ./img/context-mole.png
::::

:::{admonition} Another example for the word mole
:class: note, dropdown

```text
A mole damaged the garden.
The chemist measured one mole of the compound.
She has a mole on her cheek.
```
:::


The tokeniser may assign the same token ID to `mole` in every sentence. The
embedding lookup therefore produces the same initial vector.

The surrounding context is different, however. Transformer layers use that
context to produce a different representation of `mole` in each example.

The same principle applies when an expression changes meaning as context is
added:

```text
lion
sea lion
sea lion cuddly toy
```

::::{figure} ./img/context-sea-lion-toy.png

::::


The initial vector associated with the token `lion` is unchanged. Its
contextual representation changes because the words around it change.

:::{admonition} Embeddings vs contextual representations
:class: note

An **embedding** often refers to the initial vector produced by the embedding
layer, whereas a contextual representation is the vector associated with a
token after one or more transformer layers have processed the sequence.

Sometimes the word embedding is used to refer to both, which can be confusing.

:::

:::{important}

We need a mechanism with which to encode the position, context, and the semantic
meaning of each (sub-)word/token/embedding in the text. This is what the **transformer** architecture solves.

:::

### From representations to token probabilities

After the final transformer block, the model converts the representation at
the relevant sequence position into one score for every token in the
vocabulary. These scores are called **logits**.

Softmax turns the logits into a probability distribution:

```text
"the"        0.31
"a"          0.14
"this"       0.08
"model"      0.03
...          ...
```

A decoding strategy then selects the next token. Always choosing the most
probable token is called greedy decoding. Other strategies sample from the
distribution, possibly after adjusting it through temperature, top-k, or
top-p sampling.

The selected token is appended to the input, and the process is repeated.

```text
prompt
  -> predict one token
  -> append token
  -> predict another token
  -> append token
  -> continue until stopping
```

A fluent response is therefore constructed through repeated next-token
prediction, not by producing a complete paragraph in a single operation.

### Training pipeline

When a LLM is first trained, three steps are usually involved:

- Pretraining: the model is trained on large unstructured corpora of text, in
an unsupervised manner, just trying to predict the next token. This is what
gives origin to the base models, which understand language constructs and
syntax.
- Supervised fine-tuning (SFT): the model is trained on question-answer pairs,
possibly with reasoning traces. This is when model are actually trained to
perform a task (coding assistant, chat interface, etc.) and produces the
so-called "instruct" models.
- Reinforcement/alignment training: the model is trained using reinforcement
learning techniques, like DPO and GRPO, to influence its alignment to human
values and teach it how to reply in a way that better reflects human
preferences. After this it is usually ready to ship.

## Exercise 1: Use an LLM

To use an LLM in our code, we need to create a client.
Even though the LLM provider in our case is [AITTA](https://aitta.csc.fi), an inference service that runs LLMs on the LUMI supercomputer, we use the [OpenAI Python library](https://pypi.org/project/openai/).
AITTA implements a subset of the [OpenAI API](https://github.com/openai/openai-openapi), which has become a de facto standard for LLM APIs. This means we can easily switch to any other provider that implements the same API.

We use `AsyncOpenAI`, the asynchronous version of the client, which works with [`asyncio`](https://docs.python.org/3/library/asyncio.html). `asyncio` is Python's built-in library for running many tasks concurrently in a single program, so that while one task waits (for example, for an LLM to respond), others can keep working instead of sitting idle. This lets us send multiple requests to the LLM at the same time instead of one after another. We don't need this yet, but it will be useful in later exercises.

The `base_url` is set here to use AITTA, but it can be changed. For example, you can set it to `http://localhost:8000/v1` when running vLLM locally, or to `https://api.openai.com/v1` for OpenAI.

The API key authenticates you to the service. Keep it secret and never share it with anyone. See the [setup section](./setup.md) for how to obtain one for AITTA.


```{literalinclude} 01_hello_world.py
:end-before: async function
```

Now we can use our client to send the prompt `"Where does 'hello world' come from?"` to the model `google/gemma-4-31b-it`.

Setting `stream=True` tells the API to send the response in small pieces, called tokens, as soon as the model produces them, rather than waiting until the whole answer is finished.

We receive these pieces one at a time in the `async for` loop. Each `event` contains a `delta` with only the text that is new since the previous event. Printing with `end=""` joins the pieces into continuous text, and `flush=True` makes each one appear on screen immediately instead of being buffered.

```{literalinclude} 01_hello_world.py
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

Try changing the prompt in your editor and running the script again. Editing the code for every new prompt is a bit clumsy, so in the next part we will make it interactive, letting you type new prompts directly from the command line.

## Summary

A language model begins by dividing text into tokens. Token IDs are mapped to
initial vectors, and positional information records where those tokens occur
in the sequence.

Transformer blocks repeatedly update the representations. Attention exchanges
information between token positions. Queries and keys determine which
positions are relevant, while values contain the information that is
combined. Causal masking prevents a decoder-only model from using future
tokens.

Feed-forward layers transform each contextual representation independently.
Residual connections and normalization make it possible to train a deep stack
of these operations.

Finally, the model converts the last representation into logits and then into
a probability distribution over the vocabulary. Text generation repeats this
next-token prediction process until a stopping condition is reached.