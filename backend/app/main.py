import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import (
    activities,
    admin,
    ai,
    analytics,
    auth,
    brokers,
    emails,
    requests,
    responses,
    tasks,
)
from app.config import settings
from app.database import init_db
from app.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting Data Deletion Assistant API")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down Data Deletion Assistant API")


app = FastAPI(
    title="Data Deletion Assistant API",
    description="API for automating GDPR/CCPA data deletion requests",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - use configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Data Deletion Assistant API", "docs": "/docs", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(brokers.router, prefix="/brokers", tags=["Data Brokers"])
app.include_router(emails.router, prefix="/emails", tags=["Email Scanning"])
app.include_router(requests.router, prefix="/requests", tags=["Deletion Requests"])
app.include_router(responses.router, prefix="/responses", tags=["Broker Responses"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(tasks.router, prefix="/tasks", tags=["Background Tasks"])
app.include_router(activities.router, prefix="/activities", tags=["Activity Log"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(ai.router, prefix="/ai", tags=["AI Settings"])
