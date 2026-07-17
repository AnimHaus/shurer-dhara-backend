from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from routers.notices import router as notices_router
from routers.gallery import router as gallery_router
from routers.folders import router as folders_router
from routers.auth import router as auth_router
from routers.analytics import router as analytics_router
from routers.bg_audio import router as bg_audio_router

MONGO_URL = os.environ["MONGO_URL"]
MONGO_DB = os.environ["MONGO_DB"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    client = AsyncIOMotorClient(MONGO_URL)
    app.state.db = client[MONGO_DB]
    # Ensure indexes
    await app.state.db["news"].create_index("id", unique=True)
    await app.state.db["gallery"].create_index("id", unique=True)
    await app.state.db["gallery_folders"].create_index("id", unique=True)
    await app.state.db["gallery_folders"].create_index("slug", unique=True)
    yield
    client.close()


app = FastAPI(
    title="Shurer Dhara API",
    version="1.0.0",
    description="Centralised backend for Shurer Dhara — serves the fe-website and dashboard.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notices_router)
app.include_router(gallery_router)
app.include_router(folders_router)
app.include_router(auth_router)
app.include_router(analytics_router)
app.include_router(bg_audio_router)


@app.get("/health")
def health():
    return {"status": "ok"}
