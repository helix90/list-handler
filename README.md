# List Handler API

A FastAPI application for handling multiple lists.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the development server:
```bash
uvicorn main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## Database Setup

This application uses SQLite with SQLAlchemy and Alembic for database migrations.

### Running Migrations

To create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

To apply migrations:
```bash
alembic upgrade head
```

To rollback a migration:
```bash
alembic downgrade -1
```

## Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

