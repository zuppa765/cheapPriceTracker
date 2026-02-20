import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

SEARCH_URL = "https://allegro.pl/listing?string=kendamil%20bio%202"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text[:4000]
    })

def main():
    print("🚀 Starting price check...")

    r = requests.get(SEARCH_URL, headers=HEADERS)

    print("Status code:", r.status_code)
    print("Final URL:", r.url)
    print("Response length:", len(r.text))

    soup = BeautifulSoup(r.text, "html.parser")

    articles = soup.find_all("article")

    print("Articles found:", len(articles))

    debug_message = f"""
DEBUG INFO
Status: {r.status_code}
Final URL: {r.url}
Response length: {len(r.text)}
Articles found: {len(articles)}
"""

    # Покажем первые 2 карточки если есть
    if articles:
        debug_message += "\n\nFIRST OFFER TEXT:\n"
        debug_message += articles[0].get_text(" ", strip=True)[:1000]

    else:
        debug_message += "\n\nNO ARTICLES FOUND\n"
        debug_message += r.text[:1000]

    send_telegram(debug_message)

if __name__ == "__main__":
    main()
