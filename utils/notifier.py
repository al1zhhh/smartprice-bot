# utils/notifier.py
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def send_message(text: str):
    """Отправить сообщение в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        response = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)

        if response.status_code == 200:
            print("✅ Уведомление отправлено!")
        else:
            print(f"❌ Ошибка: {response.text}")

    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")


def notify_price_drop(title, old_price, new_price, url):
    """Уведомление о снижении цены"""
    diff = int(old_price - new_price)
    percent = round((diff / old_price) * 100, 1)

    message = (
        f"📉 <b>Цена снизилась!</b>\n\n"
        f"📦 {title}\n"
        f"💰 Было: {int(old_price)} ₸\n"
        f"✅ Стало: {int(new_price)} ₸\n"
        f"📊 Скидка: {diff} ₸ ({percent}%)\n\n"
        f"🔗 {url}"
    )
    send_message(message)


def notify_target_reached(title, price, target_price, url):
    """Уведомление когда цена достигла цели"""
    message = (
        f"🎯 <b>ЦЕЛЬ ДОСТИГНУТА!</b>\n\n"
        f"📦 {title}\n"
        f"💰 Текущая цена: {int(price)} ₸\n"
        f"🎯 Ваша цель: {int(target_price)} ₸\n\n"
        f"👉 Самое время покупать!\n"
        f"🔗 {url}"
    )
    send_message(message)


def notify_check_complete(total, dropped, reached):
    """Итоговый отчёт после проверки"""
    message = (
        f"🔍 <b>Проверка завершена</b>\n\n"
        f"📋 Всего товаров: {total}\n"
        f"📉 Подешевело: {dropped}\n"
        f"🎯 Цель достигнута: {reached}"
    )
    send_message(message)