"""FastAPI application for KEPLER Web Interface

This module provides the REST API backend that exposes KEPLER pipeline functionality
through HTTP endpoints.
"""
import logging
from datetime import datetime
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from src.api.config import APISettings
from src.api.routes import health, verification, models

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(settings: APISettings = None) -> FastAPI:
    """Create and configure the FastAPI application
    
    Args:
        settings: API settings (creates default if None)
        
    Returns:
        Configured FastAPI application
    """
    if settings is None:
        settings = APISettings()
    
    # Create FastAPI app
    app = FastAPI(
        title="KEPLER API",
        description="REST API for KEPLER fact-verification system",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Include routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(verification.router, prefix="/api", tags=["verification"])
    app.include_router(models.router, prefix="/api", tags=["models"])
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint - redirects to API documentation"""
        return {
            "message": "KEPLER API",
            "version": "1.0.0",
            "docs": "/api/docs",
            "health": "/api/health"
        }
    
    # Store settings in app state
    app.state.settings = settings
    
    logger.info(f"KEPLER API initialized on port {settings.port}")
    logger.info(f"CORS origins: {settings.cors_origins}")
    
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers for the application
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTPException with consistent error format
        
        This handler ensures all HTTP exceptions return a consistent
        error response format with error, detail, and timestamp fields.
        
        **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**
        """
        # Determine error type based on status code
        error_type_map = {
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        }
        error_type = error_type_map.get(exc.status_code, "Error")
        
        # Log the error
        if exc.status_code >= 500:
            logger.error(
                f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}",
                extra={"status_code": exc.status_code, "detail": exc.detail}
            )
        elif exc.status_code >= 400:
            logger.warning(
                f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}",
                extra={"status_code": exc.status_code, "detail": exc.detail}
            )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": error_type,
                "detail": exc.detail,
                "timestamp": datetime.now().isoformat(),
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors (400 Bad Request)
        
        This handler catches validation errors from request body validation
        and returns a structured error response with details about what failed.
        
        **Validates: Requirements 11.1, 11.4, 11.5**
        """
        error_details = []
        for error in exc.errors():
            error_details.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        
        error_message = "Request validation failed"
        logger.error(
            f"Validation error on {request.method} {request.url.path}: {error_details}",
            extra={"errors": error_details}
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Validation Error",
                "detail": error_message,
                "validation_errors": error_details,
                "timestamp": datetime.now().isoformat(),
            }
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        """Handle Pydantic model validation errors (400 Bad Request)
        
        This handler catches validation errors from Pydantic models
        and returns a structured error response.
        
        **Validates: Requirements 11.1, 11.4, 11.5**
        """
        error_details = []
        for error in exc.errors():
            error_details.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        
        logger.error(
            f"Pydantic validation error on {request.method} {request.url.path}: {error_details}",
            extra={"errors": error_details}
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Validation Error",
                "detail": "Invalid data provided",
                "validation_errors": error_details,
                "timestamp": datetime.now().isoformat(),
            }
        )
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        """Handle 404 Not Found errors
        
        This handler catches requests to non-existent endpoints
        and returns a structured error response.
        
        **Validates: Requirements 11.3, 11.4, 11.5**
        """
        logger.warning(f"404 Not Found: {request.method} {request.url.path}")
        
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "Not Found",
                "detail": f"The requested resource '{request.url.path}' was not found",
                "timestamp": datetime.now().isoformat(),
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions (500 Internal Server Error)
        
        This is the catch-all handler for any exceptions that weren't
        caught by more specific handlers. It logs the full exception
        and returns a generic error response to avoid leaking sensitive info.
        
        **Validates: Requirements 11.2, 11.4, 11.5**
        """
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
            exc_info=True,
            extra={
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An error occurred during verification. Please try again later.",
                "timestamp": datetime.now().isoformat(),
            }
        )


# Create default app instance
app = create_app()
