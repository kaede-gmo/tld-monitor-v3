import os
import cloudscraper
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
import sys

# 設定
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
NOTIFY_TO = os.environ.get("NOTIFY_TO")
URL = "https://tldes.com/com"
DATA_FILE = "last_price.txt"

def get_com_price():
    print(f"Accessing {URL}...")
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    try:
        response = scraper.get(URL, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Failed to fetch page. Content: {response.text[:200]}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        # テーブルから最安値を取得
        row = soup.select_one("table#tld-table tbody tr")
        if row:
            reg_price = row.select_one("td:nth-of-type(1)").get_text(strip=True)
            registrar = row.select_one("td.tld-registrar").get_text(strip=True)
            result = f"{reg_price} ({registrar})"
            print(f"Successfully scraped: {result}")
            return result
        else:
            print("Table row not found. The site structure might have changed.")
            return None
    except Exception as e:
        print(f"Scraping Error: {e}")
        return None

def send_email(new_price, old_price):
    if not EMAIL_USER or not EMAIL_PASS:
        print("Error: EMAIL_USER or EMAIL_PASS is not set in Secrets.")
        return

    subject = "【通知】.com ドメイン価格に変更がありました"
    body = f"tldes.comにて価格変更を検知しました。\n\n旧価格: {old_price}\n新価格: {new_price}\n\n確認はこちら: {URL}"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = NOTIFY_TO
    msg['Date'] = formatdate(localtime=True)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Email Sending Error: {e}")

def main():
    current_data = get_com_price()
    if not current_data:
        print("Failed to get current price. Exiting.")
        sys.exit(1) # ここでエラーを出して終了させる

    last_data = ""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            last_data = f.read().strip()

    print(f"Compare -> Current: [{current_data}] vs Last: [{last_data}]")

    if current_data != last_data:
        send_email(current_data, last_data)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(current_data)
        print("Price updated and saved.")
    else:
        print("No price change.")

if __name__ == "__main__":
    main()
