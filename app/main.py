"""Main application entry point for the RPX Main Backend API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP

from app.api.routes import api_router
from app.config.settings import get_settings
from app.core.auth_config import auth_config
from app.middleware.auth_middleware import AuthenticationMiddleware

# Get application settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="A FastAPI-based Python application with PostgreSQL database support for RPX loan portfolio management",
    version="0.1.0",
    debug=settings.DEBUG,
)

# Add CORS middleware with very permissive settings
# This configuration allows all origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers to the client
    max_age=3600,  # Cache preflight responses for 1 hour
)

# Add authentication middleware (only if auth is enabled)
if auth_config.AUTHENTICATION_ENABLED:
    app.add_middleware(AuthenticationMiddleware)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Initialize FastAPI-MCP
mcp = FastApiMCP(app)
mcp.mount()


@app.get("/")
async def root():
    """Root endpoint returning a simple welcome message."""
    return {"message": "Welcome to RPX Main Backend API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 