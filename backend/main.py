from contextlib import asynccontextmanager

from api.v1 import api_router
from fastapi import Depends, FastAPI
from settings.dependencies import get_db
from settings.storage import storage
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def lifespan(app: FastAPI):
    await storage.ensure_bucket()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def home():
    return {"message": "Hello World"}


@app.get("/db-check")
async def db_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT version()"))
    return {"postgres": result.scalar()}


app.include_router(api_router)
