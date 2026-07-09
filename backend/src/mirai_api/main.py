import logging
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from mirai_api import health
from mirai_api.biomarkers.router import router as biomarkers_router
from mirai_api.core.config import get_settings
from mirai_api.core.db import warm_engine
from mirai_api.lab_uploads.router import router as lab_uploads_router
from mirai_api.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uvicorn only configures its own loggers; give app loggers a handler.
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s [%(name)s] %(message)s",
    )
    await run_in_threadpool(warm_engine)
    yield


app = FastAPI(
    title="Mirai API",
    version=version("mirai-api"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(users_router)
app.include_router(lab_uploads_router)
app.include_router(biomarkers_router)
