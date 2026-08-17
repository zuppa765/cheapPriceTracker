import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo


SEARCH_URL = (
    "https://www.vinted.pl/catalog?"
    "search_text=love%20to%20dream"
    "&brand_ids[]=559556"
    "&price_to=50"
    "&currency=PLN"
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )
}

SEEN_FILE = "seen.txt"


def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        f.write("\n".join(seen))


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
        },
        timeout=30,
    )

    print(
        "Telegram message:",
        response.status_code,
        response.text,
    )


def send_telegram_photo(photo_url, caption):
    telegram_url = (
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    )

    try:
        print("Downloading image:", photo_url)

        # Download image from Vinted first
        response = requests.get(
            photo_url,
            headers=HEADERS,
            timeout=20,
        )

        response.raise_for_status()

        print(
            "Image downloaded:",
            len(response.content),
            "bytes",
        )

        # Upload actual image bytes to Telegram
        telegram_response = requests.post(
            telegram_url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
            },
            files={
                "photo": (
                    "vinted.webp",
                    response.content,
                    "image/webp",
                )
            },
            timeout=30,
        )

        print(
            "Telegram photo:",
            telegram_response.status_code,
            telegram_response.text,
        )

    except requests.RequestException as e:
        print("Image/Telegram error:", e)

        # Fallback to text message
        send_telegram(caption)


def parse_price(text):
    match = re.search(
        r"(\d+[.,]?\d*)\s*zł",
        text.lower(),
    )

    if match:
        return float(
            match.group(1).replace(",", ".")
        )

    return None


def get_image_url(parent):
    """
    Get the product image from the Vinted product container.
    """

    if not parent:
        return None

    # Vinted currently provides:
    #
    # data-testid="product-item-id-...--image--img"
    #
    # src="https://images1.vinted.net/..."

    img = parent.find(
        "img",
        attrs={
            "data-testid": lambda value:
                value and value.endswith("--image--img")
        },
    )

    if img:
        image_url = img.get("src")

        if image_url:
            return image_url

    # Fallback in case Vinted changes the data-testid
    img = parent.find("img")

    if img:
        for attr in (
            "src",
            "data-src",
            "data-lazy-src",
            "data-original",
        ):
            image_url = img.get(attr)

            if image_url:
                return image_url

    return None


def get_items():
    response = requests.get(
        SEARCH_URL,
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    # Vinted product links
    items = soup.select(
        'a[data-testid^="product-item-id"][data-testid$="--overlay-link"]'
    )

    print("Found product links:", len(items))

    results = []
    seen = load_seen()

    for item in items:

        title_attr = item.get("title", "")
        link = item.get("href")

        if not title_attr or not link:
            continue

        # Normalize link
        if link.startswith("/"):
            link = "https://www.vinted.pl" + link

        elif not link.startswith("http"):
            link = "https://www.vinted.pl/" + link

        # Already sent
        if link in seen:
            continue

        # Extract price
        price = parse_price(title_attr)

        if not price or price > 50:
            continue

        # Product title
        title = title_attr.split(",")[0]

        # Find the product container
        parent = item.find_parent(
            "div",
            class_=lambda classes:
                classes
                and any(
                    "new-item-box__container" in cls
                    for cls in classes
                ),
        )

        # Extract image
        image_url = get_image_url(parent)

        print()
        print("TITLE:", title)
        print("PRICE:", price)
        print("IMAGE:", image_url)
        print("LINK:", link)

        results.append(
            {
                "title": title,
                "price": price,
                "link": link,
                "image": image_url,
            }
        )

        seen.add(link)

    # Save only after processing all products
    save_seen(seen)

    return results


def main():
    items = get_items()

    now = datetime.now(
        ZoneInfo("Europe/Warsaw")
    )

    timestamp = now.strftime(
        "%d.%m.%Y %H:%M"
    )

    if not items:
        send_telegram(
            "⚠ Не найдено подходящих товаров."
        )
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
            print(
                "Sending image:",
                image_url,
            )

            send_telegram_photo(
                image_url,
                caption,
            )

        else:
            print(
                "No image found for:",
                title,
            )

            send_telegram(caption)


if __name__ == "__main__":
    main()
