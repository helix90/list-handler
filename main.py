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
    description="A FastAPI application for handling lists",
    version="0.1.0"
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


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to List Handler API"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

