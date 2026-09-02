from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.settings import router as settings_router
from app.api.v1.senders import router as senders_router
from app.api.v1.mess import router as mess_router
from app.api.v1.boro_khana import router as boro_khana_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.days import router as days_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.members import router as members_router
from app.api.v1.register import router as register_router
from app.api.v1.zk_demo import router as zk_demo_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.db.session import ping_url


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ping_url(settings.database_url)
    yield


app = FastAPI(title="Mess Distribution API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip().rstrip("/")
        for o in settings.cors_origins.split(",")
        if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(assignments_router)
app.include_router(days_router)
app.include_router(boro_khana_router)
app.include_router(mess_router)
app.include_router(settings_router)
app.include_router(senders_router)
app.include_router(register_router)
app.include_router(members_router)
app.include_router(zk_demo_router)
