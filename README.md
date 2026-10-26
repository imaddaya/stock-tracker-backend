# Stock Tracker Backend

FastAPI backend for the [stock tracker frontend](https://github.com/imaddaya/stock-tracker-frontend), providing authentication, portfolio membership, Alpha Vantage market data/caching and scheduled email summaries.

## Storage boundaries

PostgreSQL stores users, encrypted API keys, saved symbols, market caches and reminder records. Share quantities and purchase prices are browser-local frontend data; this API does not synchronize them across devices.

## Configure

Use Python 3.12 (CI), PostgreSQL 15 and optionally Docker Compose. Application code requires Python 3.10+.

```bash
git clone https://github.com/imaddaya/stock-tracker-backend.git
cd stock-tracker-backend/backend
cp .env.example .env
```

PowerShell: `Copy-Item .env.example .env`. Edit `.env` locally:

| Variable | Purpose |
| --- | --- |
| `EMAIL_ADDRESS`, `EMAIL_PASSWORD` | Gmail sender/app password for SMTP over TLS on port 465. |
| `JWT_SECRET` | Long random signing key. Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. |
| `API_KEY_ENCRYPTION_KEY` | After installing dependencies, generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Keep it stable for existing encrypted rows. |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Compose database credentials; replace placeholders. |
| `DATABASE_URL` | Host Python's PostgreSQL URL, normally localhost port 5432. |
| `DOCKER_DATABASE_URL` | Same database within Compose, hostname `postgres`. |
| `FRONTEND_URL` | Exact frontend origin, e.g. `http://127.0.0.1:3000`, for CORS and email links. |
| `ALPHA_VANTAGE_API_KEY` | Optional server key used to download a refreshed stock catalog. Each user supplies a separate key for market requests. |

URL-encode reserved characters in database passwords used in URLs. Keep `.env` and real credentials out of Git and chat.

## Docker setup

From `backend/`, with `.env` completed:

```bash
docker compose up --build
```

Compose waits for PostgreSQL, runs `init_db.py`, and starts the API plus a separate scheduler. Initialization creates tables, encrypts legacy plaintext keys, enforces per-user stock uniqueness and upserts the included listing CSV. Back up an existing database before applying migrations. The database uses a named volume; deleting it is not a startup repair.

The API is http://127.0.0.1:8000; Swagger is `/docs`, ReDoc `/redoc`.

## Local Python setup

Use PostgreSQL matching `DATABASE_URL`, or start the included database only:

```bash
docker compose up -d postgres
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# Generate the encryption key above and finish .env before initialization.
python init_db.py
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

PowerShell activation: `.\.venv\Scripts\Activate.ps1`. In a second terminal, activate that environment, stay in `backend/`, and run `python scheduler.py`. It checks each minute and records one delivery per user/local date. Run one scheduler instance for this demo. Uvicorn alone does not send reminders.

Start the frontend with `NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000`; visit `http://127.0.0.1:3000` so the origin matches `FRONTEND_URL`. Registration requires successful SMTP delivery; failure returns 503 and rolls back account creation.

## Refresh listings

`backend/listing_status.csv` is included for initial seeding. Configure the server-level Alpha Vantage key and run:

```bash
python import_stocks.py
```

The command validates the provider response before replacing the CSV and upserts metadata without deleting portfolio-linked records. A provider/rate-limit error preserves the old file. Previously saved symbols omitted from a newer listing remain; this command does not reconcile historical delistings.

## Tests

From `backend/`:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -v
```

Default tests use isolated SQLite and fake credentials, with email/market calls mocked. They cover authentication, token-purpose separation, signature/expiry checks, password-change invalidation, ownership, scoped caches, duplicate portfolios, POST-confirmed deletion, encryption and catalog preservation.

For PostgreSQL, set `TEST_DATABASE_URL` to a dedicated disposable test database and run the same command. The fixture creates/drops its test tables; never point it at data you need. GitHub Actions supplies a separate PostgreSQL 15 service.

Dependencies are defined in `pyproject.toml` and pinned in `uv.lock`. Regenerate pip/Docker requirements after an intentional update:

```bash
uv lock
uv export --locked --no-dev --no-emit-project --no-hashes --format requirements-txt --output-file backend/requirements.txt
uv export --locked --group dev --no-emit-project --no-hashes --format requirements-txt --output-file backend/requirements-dev.txt
```

JWT encoding/verification uses PyJWT with an explicit algorithm and required expiry/purpose claims. Standard HS256 token shapes are retained. Password creation/reset/login is limited to 72 UTF-8 bytes to prevent bcrypt truncation and oversized-input errors. An old oversized password requires a reset.

## Limits

Alpha Vantage quotas and provider availability apply. GET requests do not verify email or delete an account; those actions require POST confirmation. This is a local portfolio application; public deployment requires its own HTTPS, credential management, abuse controls and operations review.
