import aiohttp
import os

BACKEND_URL = os.getenv("BACKEND_URL")

async def ask_gpt(prompt: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/gpt", json={"prompt": prompt}) as resp:
            data = await resp.json()
            return data["answer"]
