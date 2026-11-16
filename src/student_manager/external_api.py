"""Async HTTP aggregation with retry, timeouts, task scheduling and concurrency limits."""
from __future__ import annotations
import asyncio
from collections.abc import Sequence
import httpx

async def fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    attempts: int = 3,
    timeout: float = 3.0,
    backoff: float = 0.01,
) -> dict:
    """Retry transient failures, but not terminal 4xx responses."""
    if attempts < 1 or timeout <= 0 or backoff < 0:
        raise ValueError("Некоректні параметри повторних спроб")
    for attempt in range(attempts):
        try:
            response = await asyncio.wait_for(client.get(url), timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError, TimeoutError) as exc:
            if isinstance(exc, httpx.HTTPStatusError) and 400 <= exc.response.status_code < 500:
                raise
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(backoff * (attempt + 1))
    raise RuntimeError("Недосяжний стан retry")

async def fetch_group_statistics(
    base_url: str,
    group_ids: Sequence[int],
    *,
    concurrency: int = 3,
    timeout: float = 3.0,
    attempts: int = 3,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[dict]:
    """Create Tasks and gather concurrent responses, limiting requests by semaphore."""
    if concurrency < 1:
        raise ValueError("concurrency має бути додатним")
    semaphore = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
        async def one(group_id: int) -> dict:
            async with semaphore:
                return await fetch_with_retry(
                    client, f"{base_url.rstrip('/')}/groups/{group_id}/statistics",
                    attempts=attempts, timeout=timeout,
                )
        tasks = [asyncio.create_task(one(group_id)) for group_id in group_ids]
        try:
            return list(await asyncio.gather(*tasks))
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
