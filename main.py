# main.py
import os
from utils.database import init_db, add_item, get_all_items, save_price, get_price_history
from utils.visualizer import plot_price_history
from utils.notifier import notify_price_drop, notify_target_reached, notify_check_complete, send_message
from scrapers.shop import KaspiShopScraper

TEST_URL = "https://kaspi.kz/shop/p/apple-iphone-15-128gb-nanosim-esim-chernyi-113137790/?c=710000000"


def main():
    init_db()

    items = get_all_items()
    if not items:
        add_item(
            category="shop",
            title="iPhone 15 128GB",
            url=TEST_URL,
            target_price=350000
        )
        items = get_all_items()

    # Счётчики для итогового отчёта
    total = len(items)
    dropped = 0
    reached = 0

    scraper = KaspiShopScraper()

    try:
        for item in items:
            item_id = item[0]
            title = item[2]
            url = item[3]
            target_price = item[5]
            old_price = item[4]  # current_price из прошлой проверки

            print(f"📦 {title}")
            price = scraper.get_price(url)

            if price:
                save_price(item_id, price)
                print(f"   💰 Текущая цена: {int(price)} ₸")
                print(f"   🎯 Целевая цена: {int(target_price)} ₸")

                # Проверяем снижение цены
                if old_price and price < old_price:
                    dropped += 1
                    notify_price_drop(title, old_price, price, url)

                # Проверяем достижение цели
                if price <= target_price:
                    reached += 1
                    notify_target_reached(title, price, target_price, url)
                    print(f"   ✅ ЦЕЛЬ ДОСТИГНУТА!")
                else:
                    diff = int(price - target_price)
                    print(f"   📉 До цели: {diff} ₸")

            print()

        # Итоговый отчёт в Telegram
        notify_check_complete(total, dropped, reached)

        # График
        print("📊 Строим график...")
        plot_price_history(items[0][0])

    finally:
        scraper.close()


if __name__ == "__main__":
    main()