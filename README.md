# 📈 Stock App

A user-friendly **FastAPI-based stock portfolio management system** that helps you **track your stocks**, monitor **real-time prices**, calculate **profit and loss**, and receive **email notifications** — all with efficient real-time stock data caching.

## 🛠️ Prerequisites

- Node.js and npm  
- Python 3.11 or higher  
- VS Code installed  
- Git  
- Alpha Vantage API key (get one free at [alphavantage.co](https://www.alphavantage.co/support/#api-key))

---

## ⚙️ Installation / Setup

### 📁 Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/stock-portfolio-tracker-backend.git
```
---

### 🔧 Step 2: Backend Setup

🖥️ In **Terminal**, run:

```bash
cd stock-portfolio-tracker-backend
```

📦 Create and activate a virtual environment:

**Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

📥 Install dependencies:

```bash
pip install -r requirements.txt
```

▶️ Start the backend server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🌐 Environment Variables

### 🔒 Backend `.env` file

Create a `.env` file inside the backend folder with:

```env
EMAIL_ADDRESS="your_email@example.com"
EMAIL_PASSWORD="your_gmail_app_password"
ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"
JWT_SECRET="your_jwt_secret"
JWT_ALGORITHM="HS256"
FRONTEND_URL="http://localhost:3000"
```

---

### 🔐 Gmail App Password Instructions

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Under **App Passwords**:
    - App: Mail  
    - Device: Other → type `"Stock App"`
4. Click **Generate**
5. Copy the 16-character password and use it as `EMAIL_PASSWORD`

---

### 📊 Alpha Vantage API Key

1. Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Enter your email and generate a free API key
3. Use the key as `ALPHA_VANTAGE_API_KEY`

---



