from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mirai_api.core.config import get_settings
from mirai_api.routers import health, me

app = FastAPI(title="Mirai API", version=version("mirai-api"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(me.router)
