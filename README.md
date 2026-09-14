# 📈 Stock Tracker Backend

A FastAPI backend for a stock portfolio tracking application.

The API provides user authentication, portfolio management, Alpha Vantage market data integration, stock-data caching, and scheduled email portfolio summaries.

## Features

- User registration and login
- JWT-based authentication
- Email verification
- Password reset
- Account deletion confirmation
- Per-user Alpha Vantage API keys
- Stock portfolio management
- Weekly and monthly stock market data
- Current stock quote summaries
- PostgreSQL-backed stock data caching
- Configurable email reminders
- Timezone-aware scheduled email summaries
- Restricted frontend CORS configuration
- Interactive FastAPI API documentation

## Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Pydantic Settings
- JWT authentication with `python-jose`
- bcrypt
- HTTPX
- Alpha Vantage API
- Uvicorn

## Project Structure

```text
stock-tracker-backend/
├── backend/
│   ├── cruds/
│   ├── routers/
│   ├── utils/
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── main.py
│   ├── models.py
│   ├── scheduler.py
│   ├── schemas.py
│   └── .env.example
├── pyproject.toml
└── README.md
```

## Prerequisites

Make sure you have:

- Python 3.10 or newer
- PostgreSQL
- Git
- An Alpha Vantage API key
- Email credentials if you want to use email-related features

## Installation

Clone the repository:

```bash
git clone https://github.com/imaddaya/stock-tracker-backend.git
cd stock-tracker-backend
```

Create a virtual environment.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
python -m pip install -e .
```

## Environment Configuration

Copy the example environment file.

### Windows PowerShell

```powershell
Copy-Item backend\.env.example backend\.env
```

### macOS / Linux

```bash
cp backend/.env.example backend/.env
```

Then edit `backend/.env` with your own values:

```env
EMAIL_ADDRESS=your_email@example.com
EMAIL_PASSWORD=your_email_app_password

JWT_SECRET=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256

DATABASE_URL=postgresql://stock_app:your_password@localhost:5432/stocks

FRONTEND_URL=http://127.0.0.1:3000

ALPHA_VANTAGE_API_KEY=
```

The application primarily uses the Alpha Vantage API key stored for each user account.

The server-level `ALPHA_VANTAGE_API_KEY` variable is optional.

Never commit your `.env` file or real credentials to Git.

## PostgreSQL Setup

Create a PostgreSQL user and database for the application.

Example:

```sql
CREATE USER stock_app WITH PASSWORD 'your_password';
CREATE DATABASE stocks OWNER stock_app;
```

Update `DATABASE_URL` in `backend/.env` so it matches your PostgreSQL credentials.

### Create the Database Tables

Database migrations are not currently configured, so the initial schema can be created directly from the SQLAlchemy models.

From the `backend` directory:

```bash
python -c "from database import Base, engine; import models; Base.metadata.create_all(bind=engine); print('Database tables created')"
```

The main tables are:

```text
users_table
stocks_table
portfolios_table
stock_data_cache
```

## Running the API

From the `backend` directory:

```bash
python -m uvicorn main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

ReDoc documentation:

```text
http://127.0.0.1:8000/redoc
```

## Running the Email Scheduler

The email scheduler runs separately from the FastAPI server.

Open another terminal, activate the same virtual environment, then run:

```bash
cd backend
python scheduler.py
```

The scheduler checks once per minute for users whose configured reminder time matches their current timezone.

Running it separately from the API prevents multiple web-server workers from accidentally starting duplicate scheduler instances.

## Alpha Vantage Integration

Stock market data is retrieved through the Alpha Vantage API.

Users provide their own Alpha Vantage API key, which is then used for stock-data requests.

You can obtain an API key from:

https://www.alphavantage.co/support/#api-key

The backend handles:

- Invalid stock symbols
- Provider timeouts
- API rate limits
- Malformed provider responses
- Upstream API failures

## Email Features

Email functionality is used for:

- Email verification
- Password reset
- Account deletion confirmation
- Scheduled portfolio summaries

If you use Gmail, use a Google App Password rather than your normal account password.

## Security

The backend includes:

- Password hashing with bcrypt
- JWT access tokens
- Separate token types for authentication, email verification, password reset, and account deletion
- Protected authenticated routes
- Environment-based secrets
- Restricted CORS origin
- Masked API keys in profile responses
- Cascading cleanup of user portfolio and cached stock data

## Development Status

This repository contains the backend of the Stock Tracker project.

The frontend is maintained in a separate repository.

## Author

**Imad Daya**

GitHub: https://github.com/imaddaya