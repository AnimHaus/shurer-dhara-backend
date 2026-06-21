from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

from routers.notices import router as notices_router

MONGO_URL = os.environ["MONGO_URL"]
MONGO_DB = os.environ["MONGO_DB"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    client = AsyncIOMotorClient(MONGO_URL)
    app.state.db = client[MONGO_DB]
    # Ensure index on the notices collection
    await app.state.db["news"].create_index("id", unique=True)
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


@app.get("/health")
def health():
    return {"status": "ok"}
