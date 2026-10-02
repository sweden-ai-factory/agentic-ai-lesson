import asyncio
import sys
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI


load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", default="EMPTY"),
    base_url=os.getenv("MODEL_BASE_URL", "https://aitta-api.csc.fi/openai/v1"),
)

# async function
DEFAULT_PROMPT = "Where does 'hello world' come from?"
async def main(prompt: str):
    stream = await client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="LumiOpen/Poro-34B-chat",
        stream=True,
    )

    async for event in stream:
        token = event.choices[0].delta.content
        if token:
            print(token, end="", flush=True)
    print()


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]) or DEFAULT_PROMPT
    asyncio.run(main(prompt))
