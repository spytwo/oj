from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import async_engine
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await async_engine.dispose()


app = FastAPI(title="oj", lifespan=lifespan)
