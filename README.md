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

## API Endpoints

### Core Endpoints

- `GET /` - Root endpoint
  - Returns: `{"message": "Welcome to List Handler API"}`
  
- `GET /health` - Health check endpoint
  - Returns: `{"status": "healthy"}`

### Authentication Endpoints

All authentication endpoints are under `/auth`:

- `POST /auth/register` - Register a new user
  - **Request Body:**
    ```json
    {
      "username": "string",
      "email": "email@example.com",
      "password": "string"
    }
    ```
  - **Response:** `201 Created`
    ```json
    {
      "id": 1,
      "username": "string",
      "email": "email@example.com",
      "is_active": true
    }
    ```
  - **Errors:**
    - `400 Bad Request` - Username or email already registered

- `POST /auth/login` - Login and get access token
  - **Request Body:** (form data)
    - `username`: string
    - `password`: string
  - **Response:** `200 OK`
    ```json
    {
      "access_token": "jwt_token_here",
      "token_type": "bearer"
    }
    ```
  - **Errors:**
    - `401 Unauthorized` - Incorrect username or password
    - `400 Bad Request` - User is inactive

- `POST /auth/logout` - Logout current user
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** `200 OK`
    ```json
    {
      "message": "Successfully logged out"
    }
    ```
  - **Errors:**
    - `401 Unauthorized` - Invalid or missing token

### List Endpoints

All list endpoints are under `/users/{userId}/lists` and require authentication:

- `GET /users/{userId}/lists` - Get all lists for a user
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** `200 OK`
    ```json
    [
      {
        "id": 1,
        "user_id": 1,
        "name": "Shopping List",
        "description": "My shopping list",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": null
      }
    ]
    ```
  - **Errors:**
    - `401 Unauthorized` - Missing or invalid token
    - `403 Forbidden` - User cannot access another user's lists

- `POST /users/{userId}/lists` - Create a new list
  - **Headers:** `Authorization: Bearer <token>`
  - **Request Body:**
    ```json
    {
      "name": "string",
      "description": "string"  // optional
    }
    ```
  - **Response:** `201 Created`
    ```json
    {
      "id": 1,
      "user_id": 1,
      "name": "string",
      "description": "string",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": null
    }
    ```

- `GET /users/{userId}/lists/{listId}` - Get a specific list with items
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** `200 OK`
    ```json
    {
      "id": 1,
      "user_id": 1,
      "name": "Shopping List",
      "description": "My shopping list",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": null,
      "items": [
        {
          "id": 1,
          "list_id": 1,
          "content": "Buy milk",
          "is_completed": 0,
          "created_at": "2024-01-01T00:00:00",
          "updated_at": null
        }
      ]
    }
    ```
  - **Errors:**
    - `404 Not Found` - List not found or doesn't belong to user

- `PUT /users/{userId}/lists/{listId}` - Update a list
  - **Headers:** `Authorization: Bearer <token>`
  - **Request Body:**
    ```json
    {
      "name": "string",  // optional
      "description": "string"  // optional
    }
    ```
  - **Response:** `200 OK` - Returns updated list object
  - **Errors:**
    - `404 Not Found` - List not found

- `DELETE /users/{userId}/lists/{listId}` - Delete a list
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** `204 No Content`
  - **Note:** Deleting a list also deletes all its items (cascade delete)
  - **Errors:**
    - `404 Not Found` - List not found

### List Item Endpoints

All list item endpoints are under `/users/{userId}/lists/{listId}/items` and require authentication:

- `GET /users/{userId}/lists/{listId}/items` - Get all items in a list
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** `200 OK`
    ```json
    [
      {
        "id": 1,
        "list_id": 1,
        "content": "Buy milk",
        "is_completed": 0,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": null
      }
    ]
    ```

- `POST /users/{userId}/lists/{listId}/items` - Add item to list
  - **Headers:** `Authorization: Bearer <token>`
  - **Request Body:**
    ```json
    {
      "content": "string",
      "is_completed": 0  // optional, defaults to 0 (not completed)
    }
    ```
  - **Response:** `201 Created`
    ```json
    {
      "id": 1,
      "list_id": 1,
      "content": "Buy milk",
      "is_completed": 0,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": null
    }
    ```

- `PUT /users/{userId}/lists/{listId}/items/{itemId}` - Update an item
  - **Headers:** `Authorization: Bearer <token>`
  - **Request Body:**
    ```json
    {
      "content": "string",  // optional
      "is_completed": 1  // optional (0 = not completed, 1 = completed)
    }
    ```
  - **Response:** `200 OK` - Returns updated item object
  - **Errors:**
    - `404 Not Found` - Item not found

- `DELETE /users/{userId}/lists/{listId}/items/{itemId}` - Remove an item
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** `204 No Content`
  - **Errors:**
    - `404 Not Found` - Item not found

- `PATCH /users/{userId}/lists/{listId}/items/{itemId}` - Toggle completion status
  - **Headers:** `Authorization: Bearer <token>`
  - **Response:** `200 OK` - Returns item with toggled completion status
    - Toggles `is_completed` between `0` (incomplete) and `1` (completed)
  - **Errors:**
    - `404 Not Found` - Item not found

## Authentication

Most endpoints require authentication using JWT Bearer tokens. Include the token in the request header:

```
Authorization: Bearer <your_access_token>
```

To get an access token:
1. Register a new user: `POST /auth/register`
2. Login: `POST /auth/login` (returns access token)
3. Use the token in subsequent requests

**Note:** All endpoints that access user-specific resources (lists, items) verify that the authenticated user matches the `userId` in the URL path. Users can only access their own resources.

