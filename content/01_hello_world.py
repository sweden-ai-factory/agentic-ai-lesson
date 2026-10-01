import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", default="EMPTY"),
    base_url=os.getenv("MODEL_BASE_URL", "https://aitta-api.csc.fi/openai/v1"),
)

model = OpenAIChatModel(
    os.getenv("MODEL_NAME", "google/gemma-4-31b-it"),
    provider=OpenAIProvider(openai_client=client),
)
agent = Agent(model)

prompt = "Where does 'hello world' come from?"


async def main():
    async with agent.run_stream(prompt) as result:
        print()
        async for text in result.stream_text(delta=True):
            print(text, end="", flush=True)
        print()


if __name__ == "__main__":
    asyncio.run(main())
