import asyncio
import os

from openai import AsyncOpenAI

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", default="EMPTY"),
    base_url="https://aitta-api.csc.fi/openai/v1",
)

model = OpenAIChatModel(
    "google/gemma-4-31b-it",
    provider=OpenAIProvider(openai_client=client),
)
agent = Agent(model)

prompt = "Where does 'hello world' come from?"


async def main():
    async with agent.run_stream(prompt) as result:
        print()
        async for message in result.stream_text(delta=True):
            print(message, end="")
        print()


if __name__ == "__main__":
    asyncio.run(main())
