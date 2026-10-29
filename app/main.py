from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.auth import verify_credentials
from app.database import async_engine
from app.models import Base
from app.routers.record import router as record_router
from app.routers.subtheme import router as subtheme_router
from app.routers.theme import router as theme_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await async_engine.dispose()


app = FastAPI(title="oj", lifespan=lifespan)

app.include_router(theme_router, dependencies=[Depends(verify_credentials)])
app.include_router(subtheme_router, dependencies=[Depends(verify_credentials)])
app.include_router(record_router, dependencies=[Depends(verify_credentials)])
