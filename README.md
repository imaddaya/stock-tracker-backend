# Stock App

A user-friendly FastAPI-based stock portfolio management system that helps you **track your stocks**, monitor real-time prices, calculate **profit and loss**, and receive email notifications — all with efficient real-time stock data caching.

## Features

### 🔐 User Authentication
- **User Registration & Login**: Secure account creation and authentication
- **Password Reset**: Email-based password recovery system
- **Account Management**: Profile settings and account deletion

### 📊 Stock Management
- **Stock Search**: Search for stocks by symbol or company name with autocomplete
- **Portfolio Tracking**: Add stocks to your personal portfolio
- **Real-time Data**: Fetch current stock prices and market data
- **Data Visualization**: Interactive weekly and monthly stock charts

### 💰 Portfolio Analytics
- **Quantity Tracking**: Record how many shares you own
- **Purchase Price Tracking**: Log your buy-in prices
- **Profit/Loss Calculation**: Automatic calculation of gains and losses
- **Color-coded Performance**: Visual indicators for profitable vs losing positions

### 📈 Advanced Charts
- **Weekly & Monthly Views**: Separate charts for different time periods
- **Interactive Data Points**: Click on chart points for detailed information
- **Horizontal Scrolling**: Handle large datasets with smooth scrolling
- **Custom Scaling**: Smart Y-axis scaling in multiples of 10

### ⚙️ User Settings
- **API Key Management**: Configure your Alpha Vantage API key
- **Email Reminders**: Set up daily portfolio update emails
- **Timezone Support**: Customize timezone for notifications
- **Profile Management**: Update personal information

### Prerequisites
- Node.js and npm 
- Python 3.11 or higher
- VS Code installed
- Git
- Alpha Vantage API key (get one free at [alphavantage.co](https://www.alphavantage.co/support/#api-key))

### Installation / Setup
#### 📁 Step 1: Clone the Repositories

Open different window terminals and run in each one:

`git clone https://github.com/your-username/stock-portfolio-tracker-backend.git
`git clone https://github.com/your-username/stock-portfolio-tracker-frontend.git

##### 🔧 Step 2: Backend Setup

🖥️ In **Terminal Window 1**, run the following:
`cd stock-portfolio-tracker-backend
📦 Create and activate a virtual environment:

- **Windows:**
`python -m venv venv
`.\venv\Scripts\activate

**macOS / Linux:**
`python3 -m venv venv
`source venv/bin/activate

📥 Install dependencies:
`pip install -r ../requirements.txt

▶️ Start the backend server:
`uvicorn main:app --reload --host 0.0.0.0 --port 8000

##### 💻 Step 3: Frontend Setup

🖥️ In **Terminal Window 2**, run:
`cd stock-portfolio-tracker-frontend

📥 Install dependencies:
`npm install

▶️ Start the frontend server:
`npm run dev

### Environment Variables

🧪 Create a `.env` file inside the backend folder with:
`EMAIL_ADDRESS="your_email@example.com"
`EMAIL_PASSWORD="your_gmail_app_password"
`ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"
`JWT_SECRET="your_jwt_secret"
`JWT_ALGORITHM="HS256"
`FRONTEND_URL="http://localhost:3000"

🔐 **Gmail App Password Instructions**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Under **App Passwords**:
    - App: Mail
    - Device: Other → type `"Stock App"`
4. Click **Generate**
5. Copy the 16-character password and use it as `EMAIL_PASSWORD`

📊 **Alpha Vantage API Key**
1. Visit Alpha Vantage
2. Enter your email and generate a free API key
3. Use the key as `ALPHA_VANTAGE_API_KEY`

⚙️ Create a `.env.local` file inside the frontend folder with:
`NEXT_PUBLIC_BACKEND_URL=http://localhost:8000




















