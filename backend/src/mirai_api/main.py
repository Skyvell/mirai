from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from mirai_api.core.config import get_settings
from mirai_api.core.db import warm_engine
from mirai_api.routers import biomarkers, health, lab_uploads, me


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_in_threadpool(warm_engine)
    yield


app = FastAPI(title="Mirai API", version=version("mirai-api"), lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(me.router)
app.include_router(lab_uploads.router)
app.include_router(biomarkers.router)
