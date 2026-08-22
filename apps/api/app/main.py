from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine
from app.core.error_handlers import register_exception_handlers
from app.api.v1 import genres, movies, auth, ratings
from sqlalchemy import text
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        # Hide docs in production
        docs_url="/docs" if settings.APP_ENV == "development" else None,
        redoc_url="/redoc" if settings.APP_ENV == "development" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(genres.router, prefix="/api/v1")
    app.include_router(movies.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(ratings.router, prefix="/api/v1")
    return app


app = create_app()


@app.get("/")
def root():
    return {
        "app": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }


@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Health Check Passed")
    return {"database": "connected", "status": "healthy"}