"""
Tagihan WiFi API - Core FastAPI Application

This is the main entry point for the FastAPI application.
All configuration and middleware setup is handled here.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.api.v1.api import api_router
from app.db.database import close_db

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAPI lifespan events"""
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")
    close_db()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.APP_NAME,
        description="Backend system for WiFi billing management",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "ok",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    logger.info(f"Application '{settings.APP_NAME}' initialized")
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_ENV == "development",
    )
