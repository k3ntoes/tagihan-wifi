from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import LOGGER, settings
from app.routers import paket_router, pelanggan_router, tagihan_router
from app.core.database import init_db, con

@asynccontextmanager
async def lifespan(app):
    LOGGER.info("Initializing database...")
    init_db()
    yield
    LOGGER.info("Database initialized")
    con.close()

app = FastAPI(
    title=settings.app_name,
    description="API for tagihan wifi",
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(paket_router)
app.include_router(pelanggan_router)
app.include_router(tagihan_router)
