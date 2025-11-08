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

### Local Development

Start the development server:
```bash
uvicorn main:app --reload --port 8088
```

The API will be available at:
- API: http://localhost:8088
- Interactive API docs: http://localhost:8088/docs
- Alternative API docs: http://localhost:8088/redoc

### Docker

#### Using Docker Compose (Recommended)

1. Build and start the container:
```bash
docker-compose up -d
```

2. View logs:
```bash
docker-compose logs -f
```

3. Stop the container:
```bash
docker-compose down
```

#### Using Docker directly

1. Build the image:
```bash
docker build -t list-handler-api .
```

2. Run the container:
```bash
docker run -d \
  --name list-handler-api \
  -p 8088:8088 \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY=your-secret-key-here \
  list-handler-api
```

3. Stop the container:
```bash
docker stop list-handler-api
docker rm list-handler-api
```

**Note:** The database file will be persisted in the `data/` directory when using volumes.

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

