import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from .rest.github import get_lodash_prs, router as github_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(InMemoryBackend)
    await get_lodash_prs()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(github_router)
