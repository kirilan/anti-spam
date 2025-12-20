from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import auth, brokers, emails, requests, tasks, responses, analytics, activities, admin, ai

app = FastAPI(
    title="Data Deletion Assistant API",
    description="API for automating GDPR/CCPA data deletion requests",
    version="1.0.0"
)

allowed_origins = ["*"]
if settings.environment.lower() == "production":
    allowed_origins = [settings.frontend_url.rstrip("/")]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Data Deletion Assistant API",
        "docs": "/docs",
        "version": "1.0.0"
    }


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
