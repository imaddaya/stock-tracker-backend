import os
import httpx
import smtplib
import json
from fastapi import FastAPI, HTTPException
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from stockticker.schemas import UserSignup, UserLogin, StockTicker
from email_validator import validate_email, EmailNotValidError


ALPHA_VANTAGE_API_KEY = os.environ["ALPHA_VANTAGE_API_KEY"]
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
JWT_SECRET = os.environ.get("JWT_SECRET", "your_jwt_secret_key")
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_MINUTES = 60

USERS_FILE = "users.json"


PORTFOLIO_FILE = "portfolio.json"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def is_valid_ticker(ticker: str) -> bool:
  url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
  response = httpx.get(url)
  data = response.json()
  matches = data.get("bestMatches", [])
  for match in matches:

      if match.get("1. symbol", "").upper() == ticker.upper():
          return True
  return False

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return []

def save_portfolio(portfolio_list):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio_list, f)
        
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users_dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users_dict, f)

portfolio = load_portfolio()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI is working!"}
   
@app.post("/portfolio/add")
def add_stock(stock: StockTicker):
    ticker = stock.ticker.upper()

    if not is_valid_ticker(ticker):
        raise HTTPException(status_code=400, detail="Ticker symbol does not exist")

    if ticker in portfolio:
        raise HTTPException(status_code=400, detail="Ticker already in portfolio")

    portfolio.append(ticker)
    save_portfolio(portfolio)  # Save after adding
    return {"message": f"{ticker} added to portfolio", "portfolio": portfolio}

@app.post("/portfolio/remove")
def remove_stock(stock: StockTicker):
    ticker = stock.ticker.upper()
    if ticker not in portfolio:
        raise HTTPException(status_code=404, detail="Ticker not found in portfolio")
    portfolio.remove(ticker)
    save_portfolio(portfolio)  # Save after adding
    return {"message": f"{ticker} removed from portfolio", "portfolio": portfolio}

@app.get("/portfolio")
def get_portfolio():
    return {"portfolio": portfolio}

@app.get("/portfolio/summary")
def get_portfolio_summary():
    if not portfolio:
        return {"message": "Portfolio is empty", "summary": []}

    summary = []
    for ticker in portfolio:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        try:
            response = httpx.get(url)
            data = response.json()
            quote = data.get("Global Quote", {})
            if not quote:
                summary.append({"ticker": ticker, "error": "No data returned"})
                continue
            summary.append({
                "ticker": quote.get("01. symbol", ticker),
                "price": quote.get("05. price", "N/A"),
                "change_percent": quote.get("10. change percent", "N/A")
            })
        except Exception as e:
            summary.append({"ticker": ticker, "error": str(e)})

    return {"summary": summary}

@app.post("/signup")
def signup(user: UserSignup):
    users = load_users()
    if user.email in users:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    users[user.email] = {"password": hashed_pw}
    save_users(users)

    return {"message": "User created successfully"}

@app.post("/login")
def login(user: UserLogin):
    users = load_users()
    db_user = users.get(user.email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not bcrypt.checkpw(user.password.encode("utf-8"), db_user["password"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    payload = {
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_DELTA_MINUTES)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {"access_token": token}

@app.get("/send-email")
def send_email_report():
    if not portfolio:
        return {"message": "Portfolio is empty"}

    summary = get_portfolio_summary()["summary"]

    html = "<h3>📈 Daily Stock Summary</h3>"
    html += "<table border='1' cellpadding='6' cellspacing='0'>"
    html += "<tr><th>Ticker</th><th>Price</th><th>Change %</th></tr>"

    for stock in summary:
        html += f"<tr><td>{stock.get('ticker')}</td><td>{stock.get('price')}</td><td>{stock.get('change_percent')}</td></tr>"

    html += "</table>"

    message = MIMEMultipart("alternative")
    message["Subject"] = "📊 Daily Stock Portfolio Summary"
    message["From"] = EMAIL_ADDRESS
    message["To"] = EMAIL_ADDRESS  # sends to your own email for now
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, message.as_string())
        return {"message": "Email sent successfully"}
    except Exception as e:
        return {"error": str(e)}
