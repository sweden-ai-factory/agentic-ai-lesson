import asyncio
import os

from openai import AsyncOpenAI


client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", default="EMPTY"),
    base_url="https://aitta-api.csc.fi/openai/v1",
)

# async function
async def main():
    stream = await client.chat.completions.create(
        messages=[{"role": "user", "content": "Where does 'hello world' come from?"}],
        model="google/gemma-4-31b-it",
        stream=True,
    )

    async for event in stream:
        token = event.choices[0].delta.content
        if token:
            print(token, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
