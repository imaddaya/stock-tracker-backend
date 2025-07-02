import os
import httpx
import smtplib
import json
import bcrypt
from fastapi import FastAPI, HTTPException, Query, Body, Depends, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from stockticker.schemas import UserSignup, UserLogin, StockTicker, PasswordResetRequest, EmailSchema
from email_validator import validate_email, EmailNotValidError


ALPHA_VANTAGE_API_KEY = os.environ["ALPHA_VANTAGE_API_KEY"]
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
JWT_SECRET = os.environ["JWT_SECRET"]  
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_MINUTES = 60
REPLIT_URL = os.environ.get("REPLIT_URL", "http://localhost:8000")

USERS_FILE = "users.json"
PORTFOLIO_FILE = "portfolios.json"
bearer_scheme = HTTPBearer()


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

def load_portfolios():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return {}

def save_portfolios(portfolios_dict):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolios_dict, f)
        
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users_dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users_dict, f)

def create_verification_token(email: str):
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=24),  # token valid for 24 hours
        "type": "email_verification"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def get_current_user_email(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["email"]
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
        
def create_password_reset_token(email: str):
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=1),  # shorter expiry for reset
        "type": "password_reset"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI is working!"}
   
@app.post("/portfolio/add")
def add_stock(stock: StockTicker, current_user_email: str = Depends(get_current_user_email)):
    portfolios = load_portfolios()
    user_portfolio = portfolios.get(current_user_email, [])

    ticker = stock.ticker.upper()
    if ticker in user_portfolio:
        raise HTTPException(status_code=400, detail="Ticker already in portfolio")

    user_portfolio.append(ticker)
    portfolios[current_user_email] = user_portfolio
    save_portfolios(portfolios)

    return {"message": f"{ticker} added to portfolio", "portfolio": user_portfolio}

@app.post("/portfolio/remove")
def remove_stock(stock: StockTicker, current_user_email: str = Depends(get_current_user_email)):
    portfolios = load_portfolios()
    user_portfolio = portfolios.get(current_user_email, [])

    ticker = stock.ticker.upper()
    if ticker not in user_portfolio:
        raise HTTPException(status_code=404, detail="Ticker not in portfolio")

    user_portfolio.remove(ticker)
    portfolios[current_user_email] = user_portfolio
    save_portfolios(portfolios)

    return {"message": f"{ticker} removed from portfolio", "portfolio": user_portfolio}

@app.get("/portfolio")
def get_portfolio(current_user_email: str = Depends(get_current_user_email)):
    portfolios = load_portfolios()
    return {"portfolio": portfolios.get(current_user_email, [])}

@app.get("/portfolio/summary")
def get_portfolio_summary(current_user_email: str = Depends(get_current_user_email)):
    portfolios = load_portfolios()
    user_portfolio = portfolios.get(current_user_email, [])

    if not user_portfolio:
        return {"message": "Portfolio is empty", "summary": []}

    summary = []
    for ticker in user_portfolio:
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
    try:
        valid = validate_email(user.email)
        user.email = valid.email  
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail=str(e))
    users = load_users()
    if user.email in users:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    users[user.email] = {
        "password": hashed_pw,
        "is_verified": False  
    }
    save_users(users)
    
    token = create_verification_token(user.email)
    REPLIT_URL = os.environ.get("REPLIT_URL", "http://localhost:8000")
    verification_link = f"{REPLIT_URL}/verify-email?token={token}"
    
    html = f"""
    <h3>Verify your email</h3>
    <p>Click the link below to verify your email address:</p>
    <a href="{verification_link}">{verification_link}</a>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = "Please verify your email"
    message["From"] = EMAIL_ADDRESS
    message["To"] = user.email
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, user.email, message.as_string())
    except Exception as e:
        print("Failed to send email:", e)

    return {"message": "User created successfully. Please check your email to verify your account."}

@app.post("/login")
def login(user: UserLogin):
    users = load_users()
    db_user = users.get(user.email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not bcrypt.checkpw(user.password.encode("utf-8"), db_user["password"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not db_user.get("is_verified", False):
        raise HTTPException(status_code=403, detail="Email not verified. Please verify your email before logging in.")

    payload = {
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_DELTA_MINUTES)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {"access_token": token}

@app.get("/verify-email")
def verify_email(token: str = Query(...)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "email_verification":
            raise HTTPException(status_code=400, detail="Invalid token type")
        email = payload.get("email")
        users = load_users()
        if email not in users:
            raise HTTPException(status_code=404, detail="User not found")
        users[email]["is_verified"] = True
        save_users(users)
        return {"message": "Email verified successfully!"}
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Verification token expired")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid verification token")

@app.post("/forgot-password")
def forgot_password(data: EmailSchema):
    email = data.email
    users = load_users()

    if email not in users:
        return {"message": "a password reset link has been sent."}

    if not users[email].get("is_verified", False):
        return {"message": "Email not verified. Cannot reset password."}

    token = create_password_reset_token(email)
    reset_link = f"{REPLIT_URL}/reset-password?token={token}"

    html = f"""
    <h3>Password Reset Request</h3>
    <p>Click the link below to reset your password:</p>
    <a href="{reset_link}">{reset_link}</a>
    <p>This link will expire in 1 hour.</p>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = "Password Reset Request"
    message["From"] = EMAIL_ADDRESS
    message["To"] = email
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, email, message.as_string())
    except Exception as e:
        print("Failed to send password reset email:", e)
        return {"error": "Failed to send email"}

    return {"message": "A password reset link has been sent , if there is an account associated with this email."}

@app.get("/reset-password")
def verify_reset_token(token: str = Query(...)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token type")
        email = payload.get("email")
        users = load_users()
        if email not in users:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "Token valid", "email": email}
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset token expired")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid reset token")

@app.post("/reset-password")
def reset_password(data: PasswordResetRequest):
    try:
        payload = jwt.decode(data.token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token type")
        email = payload.get("email")
        users = load_users()
        if email not in users:
            raise HTTPException(status_code=404, detail="User not found")

        hashed_pw = bcrypt.hashpw(data.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        users[email]["password"] = hashed_pw
        save_users(users)
        return {"message": "Password reset successfully"}
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset token expired")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid reset token")

@app.get("/send-email")
def send_email_report(user_email: str = Depends(get_current_user_email)):
    portfolios = load_portfolios()
    user_portfolio = portfolios.get(user_email, [])

    if not user_portfolio:
        return {"message": "Portfolio is empty"}

    summary = get_portfolio_summary(user_email)["summary"]

    html = "<h3>📈 Daily Stock Summary</h3>"
    html += "<table border='1' cellpadding='6' cellspacing='0'>"
    html += "<tr><th>Ticker</th><th>Price</th><th>Change %</th></tr>"

    for stock in summary:
        html += f"<tr><td>{stock.get('ticker')}</td><td>{stock.get('price')}</td><td>{stock.get('change_percent')}</td></tr>"

    html += "</table>"

    message = MIMEMultipart("alternative")
    message["Subject"] = "📊 Daily Stock Portfolio Summary"
    message["From"] = EMAIL_ADDRESS
    message["To"] = user_email
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, user_email, message.as_string())
        return {"message": "Email sent successfully"}
    except Exception as e:
        return {"error": str(e)}
