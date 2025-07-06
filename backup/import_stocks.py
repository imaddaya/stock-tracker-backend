import requests
import csv
import os
from sqlalchemy.orm import Session
from models import Stock
from database import SessionLocal

API_KEY = "YOUR_ALPHA_VANTAGE_KEY"
URL = f"https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={API_KEY}"
CSV_FILE = "listing_status.csv"

def download_csv():
    response = requests.get(URL)
    if response.status_code == 200:
        with open(CSV_FILE, "w", newline="") as f:
            f.write(response.text)
        print("✅ CSV downloaded.")
    else:
        print("❌ Failed to download CSV.")

def import_to_db():
    db: Session = SessionLocal()
    db.query(Stock).delete()  # Clear old records

    with open(CSV_FILE, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["status"].lower() == "active":
                stock = Stock(
                    symbol=row["symbol"],
                    name=row["name"],
                    exchange=row["exchange"],
                    asset_type=row["assetType"],
                    status=row["status"]
                )
                db.add(stock)

    db.commit()
    db.close()
    print("✅ Database updated.")

if __name__ == "__main__":
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    download_csv()
    import_to_db()
