"""Reproducible HTTPX example against FastAPI without external internet access."""
from __future__ import annotations
import asyncio
import httpx
from student_manager.api import app

async def demo() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        for path in ("/health", "/groups", "/students"):
            response = await client.get(path)
            print(f"GET {path} -> {response.status_code}: {response.json()}")

if __name__ == "__main__":
    asyncio.run(demo())
