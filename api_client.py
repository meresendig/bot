import aiohttp
import os

BACKEND_URL = os.getenv("BACKEND_URL")

async def ask_gpt(prompt: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/gpt", json={"prompt": prompt}) as resp:
            try:
                data = await resp.json()
            except Exception:
                text = await resp.text()
                return f"Ошибка на сервере: {text}"
            return data.get("answer", data.get("error", "Нет ответа от сервера"))
