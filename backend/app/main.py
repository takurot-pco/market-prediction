"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.categories import router as categories_router
from app.core.error_handlers import register_exception_handlers

app = FastAPI(
    title="Market Prediction API",
    description="Internal Prediction Market System API",
    version="0.1.0"
)

# Register exception handlers
register_exception_handlers(app)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontendのオリジン
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint"""
    return {"message": "Hello World", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}
