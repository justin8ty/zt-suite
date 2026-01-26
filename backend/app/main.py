"""FastAPI application factory and lifespan management."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.db.base import Base
from app.db.session import engine

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Configure logging, create database tables
    - Shutdown: Cleanup resources
    """
    # Startup
    setup_logging(debug=settings.debug)
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        debug=settings.debug,
    )

    # Create all database tables
    # In production, use Alembic migrations instead
    Base.metadata.create_all(bind=engine)
    logger.info("database_tables_created")

    yield

    # Shutdown
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=settings.app_name,
        description="Zero-Trust Security Suite API - Identity, Posture, and Anomaly Detection",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring."""
        return {"status": "healthy"}

    # API info endpoint
    @app.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
        }

    # Register routers here as modules are implemented
    # from app.api.routes import auth, users, devices, traffic, alerts, logs, protected
    # app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    # app.include_router(users.router, prefix="/api/users", tags=["Users"])
    # etc.

    return app


# Create application instance
app = create_app()
