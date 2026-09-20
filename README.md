# 📈 Stock Tracker Backend

A FastAPI backend for a full-stack stock portfolio tracking application.

The API provides authentication, portfolio management, Alpha Vantage market data, PostgreSQL caching, scheduled email summaries, and encrypted storage of users' Alpha Vantage API keys.

## Features

- User registration and login
- JWT-based authentication
- Email verification with explicit confirmation
- Password reset
- Account deletion with explicit confirmation
- Encrypted per-user Alpha Vantage API keys
- Stock portfolio management
- Weekly and monthly market data
- Current stock quote summaries
- PostgreSQL-backed stock-data caching
- Configurable email reminders
- Timezone-aware scheduled email summaries
- Restricted frontend CORS configuration
- FastAPI Swagger and ReDoc documentation

## Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Pydantic Settings
- JWT authentication with `python-jose`
- bcrypt
- Cryptography / Fernet encryption
- HTTPX
- Alpha Vantage API
- Uvicorn
- Docker / Docker Compose

## Related Repository

Frontend:

https://github.com/imaddaya/stock-tracker-frontend

## Project Structure

```text
stock-tracker-backend/
├── backend/
│   ├── cruds/
│   ├── routers/
│   ├── tests/
│   ├── utils/
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── init_db.py
│   ├── main.py
│   ├── models.py
│   ├── scheduler.py
│   ├── schemas.py
│   ├── requirements.txt
│   └── .env.example
├── pyproject.toml
└── README.md