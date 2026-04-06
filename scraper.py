import os
import cloudscraper
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate

# 設定 (GitHub Secretsから読み込み)
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
NOTIFY_TO = os.environ.get("NOTIFY_TO")
URL = "https://tldes.com/com"
DATA_FILE = "last_price.txt"

def get_com_price():
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # tldes.comのテーブルから最安値の行を取得
        # 1行目の1つ目のセル(Registration)とレジストラ名を取得
        row = soup.select_one("table#tld-table tbody tr")
        if row:
            reg_price = row.select_one("td:nth-of-type(1)").get_text(strip=True)
            registrar = row.select_one("td.tld-registrar").get_text(strip=True)
            return f"{reg_price} ({registrar})"
    except Exception as e:
        print(f"Error fetching price: {e}")
    return None

def send_email(new_price, old_price):
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
        print("メールを送信しました。")
    except Exception as e:
        print(f"メール送信エラー: {e}")

def main():
    current_data = get_com_price()
    if not current_data:
        print("価格の取得に失敗しました。")
        return

    # 前回データの読み込み
    last_data = ""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            last_data = f.read().strip()

    print(f"Current: {current_data} / Last: {last_data}")

    # 差分チェック
    if current_data != last_data:
        send_email(current_data, last_data)
        # 新しい価格を保存
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(current_data)
    else:
        print("価格に変更はありません。")

if __name__ == "__main__":
    main()
