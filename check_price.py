import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime, UTC
from zoneinfo import ZoneInfo

SEARCH_URL = "https://www.vinted.pl/catalog?search_text=love%20to%20dream&brand_ids[]=559556&price_to=50&currency=PLN"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SEEN_FILE = "seen.txt"

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(f.read().splitlines())
    except:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        f.write("\n".join(seen))

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    })

def send_telegram_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": photo_url,
        "caption": caption
    })

def parse_price(text):
    match = re.search(r"(\d+[.,]?\d*)\s*zł", text.lower())
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def get_items():
    r = requests.get(SEARCH_URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.select('a[data-testid^="product-item-id"]')
    results = []

    seen = load_seen()

    for item in items:
        title_attr = item.get("title", "")
        link = item.get("href")

        if not title_attr or not link:
            continue

        # normalize link
        if not link.startswith("http"):
            link = "https://www.vinted.pl" + link


        if link in seen:
            continue

        price = parse_price(title_attr)
        if not price or price > 50:
            continue

        title = title_attr.split(",")[0]

        # get image
        parent = item.find_parent("div", class_="new-item-box__container")

        img_el = None
        if parent:
            img_el = parent.find("img")

        image_url = None
        if img_el:
            image_url = img_el.get("src") or img_el.get("data-src")

        results.append({
            "title": title,
            "price": price,
            "link": link,
            "image": image_url
        })

        seen.add(link)

    save_seen(seen)

    return results



def main():
    items = get_items()

    now = datetime.now(ZoneInfo("Europe/Warsaw"))
    timestamp = now.strftime("%d.%m.%Y %H:%M")

    if not items:
        send_telegram("⚠ Не найдено подходящих товаров.")
        return

    for item in items[:5]:
        title = item["title"]
        price = item["price"]
        link = item["link"]
        image_url = item.get("image")

        caption = (
            f"🧸 Vinted alert\n"
            f"📅 {timestamp}\n"
            f"💰 {price} zł\n"
            f"{title}\n"
            f"{link}"
        )

        if image_url:
            print("IMAGE:", image_url)
            send_telegram_photo(image_url, caption)
        else:
            send_telegram(caption)


if __name__ == "__main__":
    main()
