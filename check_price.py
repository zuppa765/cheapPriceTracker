import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

SEARCH_URL = "https://allegro.pl/listing?string=kendamil%20bio%202"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    })


def get_lowest_price():
    r = requests.get(SEARCH_URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    prices = []

    for text in soup.stripped_strings:
        match = re.search(r"(\d+[.,]\d+)\s*zł\s*/\s*100\s*g", text)
        if match:
            price = float(match.group(1).replace(",", "."))
            prices.append(price)

    return min(prices) if prices else None


def main():
    lowest = get_lowest_price()

    today = datetime.utcnow().strftime("%d.%m.%Y")

    if lowest:
        send_telegram(
            f"🍼 Kendamil Bio 2\n"
            f"📅 {today}\n"
            f"💰 Самая дешёвая цена: {lowest} zł / 100g\n"
            f"🔎 {SEARCH_URL}"
        )
    else:
        send_telegram(
            f"⚠ Не удалось найти цену\n{SEARCH_URL}"
        )


if __name__ == "__main__":
    main()
