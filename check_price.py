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


def extract_weight(title):
    match = re.search(r"(\d+)\s?g", title.lower())
    if match:
        return int(match.group(1))
    return None


def get_lowest_price():
    r = requests.get(SEARCH_URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    offers = soup.find_all("article")

    lowest_price_100g = None

    for offer in offers:
        text = offer.get_text(" ", strip=True)

        # ищем цену
        price_match = re.search(r"(\d+[.,]\d+)\s*zł", text)
        if not price_match:
            continue

        price = float(price_match.group(1).replace(",", "."))

        # ищем вес
        weight = extract_weight(text)
        if not weight:
            continue

        price_per_100g = (price / weight) * 100

        if lowest_price_100g is None or price_per_100g < lowest_price_100g:
            lowest_price_100g = round(price_per_100g, 2)

    return lowest_price_100g


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
        send_telegram("⚠ Не удалось найти предложения.")


if __name__ == "__main__":
    main()
