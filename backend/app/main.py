"""
FastAPI main application for LeetCoach backend.
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .routers import agents_router, screen_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.value),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting LeetCoach backend...")
    
    # Validate configuration
    try:
        if not settings.validate_llm_config():
            logger.warning("LLM configuration is incomplete")
        else:
            logger.info(f"LLM provider configured: {settings.default_llm_provider}")
        
        if not settings.validate_vector_db_config():
            logger.warning("Vector database configuration is incomplete")
        else:
            logger.info("Vector database configured")
            
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
    
    logger.info("LeetCoach backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down LeetCoach backend...")


# Create FastAPI application
app = FastAPI(
    title="LeetCoach API",
    description="AI-powered coding assistant for LeetCode integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Custom exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Request validation failed",
            "details": exc.errors(),
            "status_code": 422,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": str(exc) if settings.log_level.value == "DEBUG" else "An error occurred",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = datetime.utcnow()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    duration = (datetime.utcnow() - start_time).total_seconds() * 1000
    logger.info(f"Response: {response.status_code} ({duration:.2f}ms)")
    
    return response


# Include routers
app.include_router(agents_router)
app.include_router(screen_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "name": "LeetCoach API",
        "version": "1.0.0",
        "description": "AI-powered coding assistant for LeetCode integration",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/api/health",
            "docs": "/docs",
            "agents": {
                "ask": "/api/ask",  # New dynamic endpoint
                "optimize": "/api/optimize",
                "complexity": "/api/complexity",
                "hint": "/api/hint",
                "counter_questions": "/api/counter-questions",
                "deep_questions": "/api/deep-questions",
                "solution": "/api/solution",
                "batch": "/api/batch"
            },
            "user": {
                "preferences": "/api/user/{user_id}/preferences",
                "history": "/api/user/{user_id}/history"
            },
            "providers": "/api/providers"
        }
    }


# Additional utility endpoints
@app.get("/info")
async def get_info():
    """Get detailed application information."""
    return {
        "application": {
            "name": "LeetCoach Backend",
            "version": "1.0.0",
            "description": "Modular AI-powered coding assistant",
            "author": "LeetCoach Team"
        },
        "configuration": {
            "llm_provider": settings.default_llm_provider.value,
            "log_level": settings.log_level.value,
            "cors_enabled": len(settings.cors_origins) > 0,
            "vector_db_enabled": settings.validate_vector_db_config()
        },
        "agents": [
            "optimize", "complexity", "hint", 
            "counter", "deepq", "solution"
        ],
        "supported_languages": [
            "python", "javascript", "java", "cpp", 
            "c", "csharp", "go", "rust", "typescript"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.value.lower()
    )
