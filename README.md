# Authentication API

A modern, scalable authentication API built with FastAPI, MySQL, and Redis.

## Features

- User authentication with JWT tokens
- Redis caching
- MySQL database
- Async/await for better performance
- Comprehensive error handling
- Type hints and Pydantic models
- Clean architecture

## Tech Stack

- FastAPI 0.104.1
- MySQL with aiomysql
- Redis with aioredis
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
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/auth_app
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0
JWT_SECRET_KEY=your_jwt_secret
JWT_REFRESH_SECRET_KEY=your_jwt_refresh_secret
```

4. Run the application:

```bash
uvicorn main:app --reload
```

## API Endpoints

### Authentication

- `POST /auth/signup` - Register a new user
- `POST /auth/login` - Login and get access token
- `POST /auth/refresh` - Refresh access token
- `GET /auth/user` - Get current user info

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
