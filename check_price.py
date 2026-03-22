import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

SEARCH_URL = "https://www.vinted.pl/catalog?search_text=love%20to%20dream&brand_ids[]=559556&price_to=50&currency=PLN"

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


def parse_price(text):
    match = re.search(r"(\d+[.,]?\d*)\s*zł", text.lower())
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def get_items():
    r = requests.get(SEARCH_URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.find_all("a", href=True)

    results = []

    for item in items:
        text = item.get_text(" ", strip=True)

        price = parse_price(text)
        if not price:
            continue

        # filter price <= 50 PLN
        if price > 50:
            continue

        title = text[:120]
        link = item["href"]

        if not link.startswith("http"):
            link = "https://www.vinted.pl" + link

        results.append({
            "title": title,
            "price": price,
            "link": link
        })

    return results


def main():
    items = get_items()
    today = datetime.utcnow().strftime("%d.%m.%Y")

    if not items:
        send_telegram("⚠ Не найдено подходящих товаров.")
        return

    for item in items[:5]:  # limit spam
        msg = (
            f"🧸 Vinted alert\n"
            f"💰 {item['price']} zł\n"
            f"{item['title']}\n"
            f"🔗 {item['link']}"
        )
        send_telegram(msg)


if __name__ == "__main__":
    main()
