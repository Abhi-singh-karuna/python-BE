# Activity App Backend

A modern, scalable backend API for the Activity App built with FastAPI, PostgreSQL, and Redis.

## Features

- User authentication with JWT tokens
- Email verification system
- Redis caching
- PostgreSQL database
- Async/await for better performance
- Comprehensive error handling
- Type hints and Pydantic models
- Clean architecture

## Tech Stack

- FastAPI 0.104.1
- PostgreSQL with asyncpg
- Redis with aioredis
- SendGrid for email services
- Pydantic for data validation
- Python 3.8+

## Project Structure

```
.
├── config/             # Configuration files
├── controller/         # API controllers
├── model/             # Pydantic models
├── repository/        # Database repositories
├── service/           # Business logic
├── utils/             # Utility functions
├── middleware/        # FastAPI middleware
├── router/            # API routes
├── migration/         # Database migrations
├── templates/         # Email templates
├── tests/             # Unit tests
├── main.py           # Application entry point
└── requirements.txt   # Project dependencies
```

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

3. Create a `.env` file with the following variables:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0
JWT_SECRET_KEY=your_jwt_secret
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=your_email@example.com
SENDGRID_FROM_NAME=Your Name
WEB_URL=http://localhost:3000
```

4. Run the application:

```bash
uvicorn main:app --reload
```

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run the tests with pytest:

```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
