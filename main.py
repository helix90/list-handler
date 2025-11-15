from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, lists, items
import subprocess

# Create database tables
Base.metadata.create_all(bind=engine)

# Run database migrations on startup
try:
    subprocess.run(["alembic", "upgrade", "head"], check=True)
except subprocess.CalledProcessError:
    # If migrations fail, continue anyway (might be first run)
    pass
except FileNotFoundError:
    # Alembic not available, skip migrations
    pass

app = FastAPI(
    title="List Handler API",
    description="A FastAPI application for handling multiple lists with authentication. Users can create lists and manage list items with completion tracking.",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(lists.router)
app.include_router(items.router)


@app.get(
    "/",
    summary="Root endpoint",
    description="Welcome endpoint that returns API information",
    tags=["core"]
)
async def root():
    """
    Root endpoint of the API.
    
    Returns a welcome message.
    """
    return {"message": "Welcome to List Handler API"}


@app.get(
    "/health",
    summary="Health check",
    description="Health check endpoint for monitoring and load balancers",
    tags=["core"],
    responses={
        200: {"description": "Service is healthy"}
    }
)
async def health_check():
    """
    Health check endpoint.
    
    Used by monitoring systems and load balancers to verify the service is running.
    Returns a simple status indicator.
    """
    return {"status": "healthy"}

