from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import auth, email, portfolio, stock_search, user


settings = get_settings()

app = FastAPI(
    title="Stock Portfolio Tracker API",
    description=(
        "Backend API for managing stock portfolios, "
        "market data, authentication, and email reminders."
    ),
    version="1.0.0",
)

frontend_origin = settings.FRONTEND_URL.rstrip("/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(email.router)
app.include_router(portfolio.router)
app.include_router(stock_search.router)
app.include_router(user.router)


@app.get("/")
def root():
    return {
        "message": "Stock Portfolio Tracker API is running"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )