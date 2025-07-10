import requests
import csv
import os
from sqlalchemy.orm import Session
from models import StocksTable
from database import SessionLocal

ALPHA_VANTAGE_API_KEY = os.environ["ALPHA_VANTAGE_API_KEY"]
URL = f"https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={ALPHA_VANTAGE_API_KEY}"

# Get the absolute path to this script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "listing_status.csv")

def download_csv():
    response = requests.get(URL)
    if response.status_code == 200:
        with open(CSV_FILE, "w", newline="") as f:
            f.write(response.text)
        print("✅ CSV downloaded.")
    else:
        print("❌ Failed to download CSV.")

def import_csvfile_to_db():
    db: Session = SessionLocal()
    db.query(StocksTable).delete()  # Clear old records

    with open(CSV_FILE, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["status"].lower() == "active":
                stock = StocksTable(
                    symbol=row["symbol"],
                    name=row["name"],
                    is_listed=True
                )
                db.add(stock)

    db.commit()
    db.close()
    print("✅ Database updated.")

if __name__ == "__main__":
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    download_csv()
    import_csvfile_to_db()
