# Pro-Policy App Backend

A modern, scalable backend service for policy management built with FastAPI, PostgreSQL, and Redis, following clean architecture principles.

## Architecture Overview

The application follows a clean architecture pattern with clear separation of concerns:

```
.
├── config/             # Configuration management
├── controller/         # Request handlers and response formatters
├── model/             # Data models and schemas
├── repository/        # Database access layer
├── service/           # Business logic layer
├── utils/             # Utility functions and helpers
├── middleware/        # FastAPI middleware components
├── router/            # API route definitions
├── database/          # Database connection management
├── tests/             # Test suite
├── main.py           # Application entry point
└── requirements.txt   # Project dependencies
```

### Key Components

- **Controllers**: Handle HTTP requests and responses, implement input validation
- **Services**: Contain business logic and orchestrate operations
- **Repositories**: Manage data access and persistence
- **Models**: Define data structures and validation rules
- **Middleware**: Handle cross-cutting concerns like CORS, logging, and authentication

## Features

- RESTful API endpoints for policy management
- JWT-based authentication
- PostgreSQL database with connection pooling
- Redis caching for improved performance
- Comprehensive error handling and logging
- Docker containerization
- Health check endpoints
- CORS middleware support
- Request validation using Pydantic
- Async/await for better performance

## Tech Stack

- FastAPI 0.104.1
- PostgreSQL with asyncpg
- Redis with aioredis
- Pydantic 2.4.2 for data validation
- Python 3.10+
- Docker for containerization

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- PostgreSQL
- Redis

## Setup and Installation

### Local Development

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment:

   - Copy `config/config.yml.example` to `config/config.yml`
   - Update the configuration values as needed

4. Run the application:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

1. Build and run using Docker Compose:

```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

## API Endpoints

### Common Endpoints

- `GET /healthz` - Health check endpoint
- `GET /terms-of-service` - Get terms of service

### Authentication

- `POST /auth/signup` - Register a new user
- `POST /auth/login` - User login (commented out in current version)
- `POST /auth/refresh` - Refresh token (commented out in current version)

### User Management

- `GET /user/` - Get current user info
- `GET /user/email` - Get user by email

## API Documentation

Once the application is running, access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Error Handling

The application implements comprehensive error handling:

- Custom exception handlers for validation errors
- Structured error responses
- Detailed logging of errors
- Middleware for request/response logging

## Logging

Logging is implemented using a custom Logger class that:

- Supports different log levels
- Includes request context
- Provides structured logging output
- Can be configured for different environments

## Testing

Run the test suite:

```bash
pytest
```

## Deployment

The application is containerized using Docker:

- Multi-stage build for optimized image size
- Non-root user for security
- Environment variable configuration
- Health check endpoints for monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
