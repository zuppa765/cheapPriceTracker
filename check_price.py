import requests
from bs4 import BeautifulSoup
import re
import os

SEARCH_URL = "https://allegro.pl/listing?string=kendamil%20bio%202"
PRICE_LIMIT = 8.50  # zł за 100g

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

    if lowest and lowest < PRICE_LIMIT:
        send_telegram(
            f"🔥 Kendamil Bio 2 подешевел!\n"
            f"{lowest} zł / 100g\n"
            f"{SEARCH_URL}"
        )


if __name__ == "__main__":
    main()
