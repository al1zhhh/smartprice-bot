# bot.py
import logging
import pytz
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from utils.database import init_db, add_item, get_all_items, save_price, get_price_history, export_to_csv, get_all_users
from utils.visualizer import plot_price_history
from scrapers.shop import KaspiShopScraper
from scrapers.travels import TravelsScraper
from scrapers.realty import KrishaScraper
from scrapers.auto import KolesaScraper
from config import TELEGRAM_TOKEN
from apscheduler.schedulers.background import BackgroundScheduler
from config import CHECK_INTERVAL
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
import threading
import time
import os

# Логирование
logging.basicConfig(level=logging.INFO)

# Состояния для добавления товара
CATEGORY, TITLE, URL, TARGET_PRICE = range(4)


# Главное меню
def main_menu():
    keyboard = [
        [KeyboardButton("📋 Все товары"), KeyboardButton("➕ Добавить товар")],
        [KeyboardButton("🔍 Проверить цены"), KeyboardButton("📊 Графики")],
        [KeyboardButton("🗑️ Удалить товар"), KeyboardButton("📈 Отчёт")],
        [KeyboardButton("🔎 Проверить один товар"), KeyboardButton("📥 Экспорт CSV")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Привет! Я *SmartPrice Bot*\n\n"
        "Слежу за ценами на товары и билеты, "
        "и сообщу когда цена упадёт до нужного уровня!\n\n"
        "Выбери действие 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# /help
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📖 *SmartPrice Bot — команды:*\n\n"
        "/start — Главное меню\n"
        "/help — Помощь\n"
        "/status — Статус всех товаров\n"
        "/check — Проверить цены прямо сейчас\n"
        "/report — Ежедневный отчёт\n\n"
        "Или используй кнопки меню 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# Показать все товары
def show_all_items(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    items = get_all_items(user_id)
    if not items:
        update.message.reply_text(
            "📋 Список товаров пуст!\n\nНажми ➕ Добавить товар",
            reply_markup=main_menu()
        )
        return

    message = "📋 *Отслеживаемые товары:*\n\n"
    for item in items:
        current = f"{int(item[5])} ₸" if item[5] else "не проверялась"
        emoji_map = {"shop": "🛍️", "travel": "✈️", "realty": "🏠", "auto": "🚗"}
        emoji = emoji_map.get(item[2], "📦")

        message += (
            f"{emoji} *{item[3]}*\n"
            f"   💰 Текущая: {current}\n"
            f"   🎯 Целевая: {int(item[6])} ₸\n"
            f"   🆔 ID: {item[0]}\n\n"
        )

    update.message.reply_text(message, parse_mode="Markdown", reply_markup=main_menu())


# Добавить товар — шаг 1
def add_item_start(update: Update, context: CallbackContext):
    keyboard = [
        [KeyboardButton("🛍️ Магазин"), KeyboardButton("✈️ Авиабилеты")],
        [KeyboardButton("🏠 Недвижимость"), KeyboardButton("🚗 Авто")],
        [KeyboardButton("❌ Отмена")]
    ]
    update.message.reply_text(
        "➕ *Добавить новый товар*\n\nВыбери категорию:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CATEGORY


# Шаг 2 — категория выбрана
def get_category(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "🛍️ Магазин":
        context.user_data["category"] = "shop"
    elif text == "✈️ Авиабилеты":
        context.user_data["category"] = "travel"
    elif text == "🏠 Недвижимость":
        context.user_data["category"] = "realty"
    elif text == "🚗 Авто":
        context.user_data["category"] = "auto"

    update.message.reply_text("Введи название товара:")
    return TITLE


# Шаг 3 — название
def get_title(update: Update, context: CallbackContext):
    if update.message.text == "❌ Отмена":
        update.message.reply_text("Отменено", reply_markup=main_menu())
        return ConversationHandler.END


    context.user_data["title"] = update.message.text
    update.message.reply_text("Вставь ссылку на товар:")
    return URL


# Шаг 4 — ссылка
def get_url(update: Update, context: CallbackContext):
    if update.message.text == "❌ Отмена":
        update.message.reply_text("Отменено", reply_markup=main_menu())
        return ConversationHandler.END

    context.user_data["url"] = update.message.text
    update.message.reply_text("Введи целевую цену в тенге (например: 350000):")
    return TARGET_PRICE



# Шаг 5 — целевая цена и сохранение
def get_target_price(update: Update, context: CallbackContext):
    if update.message.text == "❌ Отмена":
        update.message.reply_text("Отменено", reply_markup=main_menu())
        return ConversationHandler.END
    try:
        target_price = float(update.message.text)
    except ValueError:
        update.message.reply_text("❌ Введи число! Например: 350000")
        return TARGET_PRICE

    # Проверяем лимит
    items = get_all_items()
    if len(items) >= 10:
        update.message.reply_text(
            "⚠️ *Достигнут лимит товаров!*\n\n"
            "Максимум 10 товаров одновременно.\n"
            "Удали ненужный товар через 🗑️ Удалить товар",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return ConversationHandler.END

    category = context.user_data["category"]
    title = context.user_data["title"]
    url = context.user_data["url"]

    user_id = update.message.from_user.id
    add_item(user_id, category, title, url, target_price)
    update.message.reply_text(
        f"✅ *Товар добавлен!*\n\n"
        f"📦 {title}\n"
        f"🎯 Целевая цена: {int(target_price)} ₸",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    return ConversationHandler.END


# Отмена
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Отменено", reply_markup=main_menu())
    return ConversationHandler.END

# Проверить цены
def check_prices(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    items = get_all_items(user_id)
    if not items:
        update.message.reply_text("❌ Нет товаров для проверки", reply_markup=main_menu())
        return

    update.message.reply_text("🔍 Начинаю проверку цен... Подожди немного!")

    shop_items = [i for i in items if i[2] == "shop"]
    travel_items = [i for i in items if i[2] == "travel"]

    results = ""

    if shop_items:
        scraper = KaspiShopScraper()
        try:
            for item in shop_items:
                price = scraper.get_price(item[4])
                if price:
                    save_price(item[0], price)
                    diff = int(price - item[6])
                    status = "✅ ЦЕЛЬ!" if price <= item[6] else f"📉 до цели: {diff} ₸"
                    results += f"🛍️ *{item[3]}*\n💰 {int(price)} ₸ — {status}\n\n"
        finally:
            scraper.close()

    if travel_items:
        scraper = TravelsScraper()
        try:
            for item in travel_items:
                price = scraper.get_price(item[4])
                if price:
                    save_price(item[0], price)
                    diff = int(price - item[6])
                    status = "✅ ЦЕЛЬ!" if price <= item[6] else f"📉 до цели: {diff} ₸"
                    results += f"✈️ *{item[3]}*\n💰 {int(price)} ₸ — {status}\n\n"
        finally:
            scraper.close()
    realty_items = [i for i in items if i[2] == "realty"]
    auto_items = [i for i in items if i[2] == "auto"]

    if realty_items:
        scraper = KrishaScraper()
        try:
            for item in realty_items:
                price = scraper.get_price(item[4])
                if price:
                    save_price(item[0], price)
                    diff = int(price - item[6])
                    status = "✅ ЦЕЛЬ!" if price <= item[6] else f"📉 до цели: {diff} ₸"
                    results += f"🏠 *{item[3]}*\n💰 {int(price)} ₸ — {status}\n\n"
        finally:
            scraper.close()

    if auto_items:
        scraper = KolesaScraper()
        try:
            for item in auto_items:
                price = scraper.get_price(item[4])
                if price:
                    save_price(item[0], price)
                    diff = int(price - item[6])
                    status = "✅ ЦЕЛЬ!" if price <= item[6] else f"📉 до цели: {diff} ₸"
                    results += f"🚗 *{item[3]}*\n💰 {int(price)} ₸ — {status}\n\n"
        finally:
            scraper.close()

    update.message.reply_text(
        f"🔍 *Результаты проверки:*\n\n{results}",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

def check_single_item(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    items = get_all_items(user_id)

    if not items:
        update.message.reply_text("❌ Нет товаров", reply_markup=main_menu())
        return

    message = "🔎 Выбери ID товара для проверки:\n\n"
    for item in items:
        emoji_map = {"shop": "🛍️", "travel": "✈️", "realty": "🏠", "auto": "🚗"}
        emoji = emoji_map.get(item[2], "📦")
        current = f"{int(item[5])} ₸" if item[5] else "не проверялся"
        message += f"{emoji} [{item[0]}] {item[3]} — {current}\n"

    message += "\nНапиши ID товара:"
    update.message.reply_text(message, reply_markup=main_menu())
    context.user_data["waiting_single_check_id"] = True
# График
def show_chart(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    items = get_all_items(user_id)

    if not items:
        update.message.reply_text("❌ Нет товаров", reply_markup=main_menu())
        return

    message = "📊 Выбери ID товара для графика:\n\n"
    for item in items:
        message += f"  [{item[0]}] {item[3]}\n"
    message += "\nНапиши ID товара:"

    update.message.reply_text(message, reply_markup=main_menu())
    context.user_data["waiting_chart_id"] = True


# Удалить товар
def delete_item_cmd(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    items = get_all_items(user_id)

    if not items:
        update.message.reply_text("❌ Нет товаров", reply_markup=main_menu())
        return

    message = "🗑️ Напиши ID товара для удаления:\n\n"
    for item in items:
        message += f"  [{item[0]}] {item[3]}\n"

    update.message.reply_text(message, reply_markup=main_menu())
    context.user_data["waiting_delete_id"] = True


# Ежедневный отчёт
def daily_report(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    items = get_all_items(user_id)
    if not items:
        update.message.reply_text("❌ Нет товаров", reply_markup=main_menu())
        return

    message = "📈 *Ежедневный отчёт*\n\n"

    for item in items:
        history = get_price_history(item[0])
        emoji_map = {"shop": "🛍️", "travel": "✈️", "realty": "🏠", "auto": "🚗"}
        emoji = emoji_map.get(item[2], "📦")
        current = f"{int(item[5])} ₸" if item[5] else "нет данных"

        if len(history) >= 2:
            first_price = history[0][0]
            last_price = history[-1][0]
            change = int(last_price - first_price)
            trend = "📈" if change > 0 else "📉"
            change_text = f"{trend} {abs(change)} ₸"
        else:
            change_text = "недостаточно данных"

        message += (
            f"{emoji} *{item[3]}*\n"
            f"   💰 Текущая: {current}\n"
            f"   🎯 Целевая: {int(item[6])} ₸\n"
            f"   📊 Изменение: {change_text}\n\n"
        )

    update.message.reply_text(message, parse_mode="Markdown", reply_markup=main_menu())


# Обработка текстовых сообщений
def handle_message(update: Update, context: CallbackContext):
    text = update.message.text

    if text == "📋 Все товары":
        show_all_items(update, context)
    elif text == "➕ Добавить товар":
        add_item_start(update, context)
    elif text == "🔍 Проверить цены":
        check_prices(update, context)
    elif text == "📊 Графики":
        show_chart(update, context)
    elif text == "🗑️ Удалить товар":
        delete_item_cmd(update, context)
    elif text == "📈 Отчёт":
        daily_report(update, context)
    elif text == "🔎 Проверить один товар":
        check_single_item(update, context)
    elif text == "📥 Экспорт CSV":
        export_csv(update, context)
    # Обработка ID для графика
    elif context.user_data.get("waiting_chart_id"):
        try:
            item_id = int(text)
            context.user_data["waiting_chart_id"] = False

            filename = f"data/price_chart_{item_id}.png"
            plot_price_history(item_id)

            if os.path.exists(filename):
                with open(filename, "rb") as photo:
                    update.message.reply_photo(photo, caption=f"📊 График цен")
            else:
                update.message.reply_text("⚠️ Нет данных для графика")
        except ValueError:
            update.message.reply_text("❌ Введи число!")
    elif context.user_data.get("waiting_single_check_id"):
        try:
            item_id = int(text)
            context.user_data["waiting_single_check_id"] = False

            user_id = update.message.from_user.id
            items = get_all_items(user_id)  # ← добавили user_id
            item = next((i for i in items if i[0] == item_id), None)

            if not item:
                update.message.reply_text("❌ Товар с таким ID не найден", reply_markup=main_menu())
                return

            update.message.reply_text(f"🔍 Проверяю цену для: *{item[3]}*...", parse_mode="Markdown")  # ← item[3] title

            category = item[2]  # ← item[2] category
            scraper_map = {
                "shop": KaspiShopScraper,
                "travel": TravelsScraper,
                "realty": KrishaScraper,
                "auto": KolesaScraper,
            }

            scraper_class = scraper_map.get(category)
            if not scraper_class:
                update.message.reply_text("❌ Неизвестная категория", reply_markup=main_menu())
                return

            scraper = scraper_class()
            try:
                price = scraper.get_price(item[4])  # ← item[4] url
                if price:
                    save_price(item[0], price)
                    diff = int(price - item[6])  # ← item[6] target_price
                    status = "✅ ЦЕЛЬ ДОСТИГНУТА!" if price <= item[6] else f"📉 До цели: {diff} ₸"
                    emoji_map = {"shop": "🛍️", "travel": "✈️", "realty": "🏠", "auto": "🚗"}
                    emoji = emoji_map.get(category, "📦")

                    update.message.reply_text(
                        f"{emoji} *{item[3]}*\n"  # ← item[3] title
                        f"💰 Цена: {int(price)} ₸\n"
                        f"🎯 Цель: {int(item[6])} ₸\n"  # ← item[6] target_price
                        f"{status}\n\n"
                        f"🔗 [Открыть товар]({item[4]})",  # ← item[4] url
                        parse_mode="Markdown",
                        reply_markup=main_menu(),
                        disable_web_page_preview=True
                    )
                else:
                    update.message.reply_text("⚠️ Не удалось получить цену", reply_markup=main_menu())
            finally:
                scraper.close()

        except ValueError:
            update.message.reply_text("❌ Введи число!", reply_markup=main_menu())
    elif context.user_data.get("waiting_export_id"):
        try:
            item_id = int(text)
            context.user_data["waiting_export_id"] = False

            filepath = f"data/export_{item_id}.csv"
            result = export_to_csv(item_id, filepath)

            if result:
                with open(filepath, "rb") as f:
                    update.message.reply_document(
                        f,
                        filename=f"price_history_{item_id}.csv",
                        caption="📥 История цен"
                    )
            else:
                update.message.reply_text(
                    "⚠️ Нет данных для экспорта",
                    reply_markup=main_menu()
                )
        except ValueError:
            update.message.reply_text("❌ Введи число!", reply_markup=main_menu())
    # Обработка ID для удаления
    elif context.user_data.get("waiting_delete_id"):
        try:
            item_id = int(text)
            context.user_data["waiting_delete_id"] = False

            from utils.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tracked_items WHERE id = ?", (item_id,))
            cursor.execute("DELETE FROM price_history WHERE item_id = ?", (item_id,))
            conn.commit()
            conn.close()

            update.message.reply_text(f"✅ Товар удалён!", reply_markup=main_menu())
        except ValueError:
            update.message.reply_text("❌ Введи число!")


def auto_check(bot):
    """Автоматическая проверка для всех пользователей"""
    users = get_all_users()
    if not users:
        return

    print(f"⏰ Автопроверка — {len(users)} пользователей")

    for user_id in users:
        items = get_all_items(user_id)
        if not items:
            continue

        # индексы сдвинулись из-за user_id — теперь:
        # item[0]=id, item[1]=user_id, item[2]=category,
        # item[3]=title, item[4]=url, item[5]=current_price, item[6]=target_price

        shop_items = [i for i in items if i[2] == "shop"]
        travel_items = [i for i in items if i[2] == "travel"]
        realty_items = [i for i in items if i[2] == "realty"]
        auto_items = [i for i in items if i[2] == "auto"]

        scraper_groups = [
            (shop_items, KaspiShopScraper, "🛍️"),
            (travel_items, TravelsScraper, "✈️"),
            (realty_items, KrishaScraper, "🏠"),
            (auto_items, KolesaScraper, "🚗"),
        ]

        for group_items, ScraperClass, emoji in scraper_groups:
            if not group_items:
                continue

            scraper = ScraperClass()
            try:
                for item in group_items:
                    item_id = item[0]
                    title = item[3]
                    url = item[4]
                    target_price = item[6]
                    old_price = item[5]

                    price = scraper.get_price(url)
                    if not price:
                        continue

                    save_price(item_id, price)

                    if old_price and price < old_price:
                        diff = int(old_price - price)
                        percent = round((diff / old_price) * 100, 1)
                        bot.send_message(
                            chat_id=user_id,
                            text=(
                                f"📉 <b>Цена снизилась!</b>\n\n"
                                f"{emoji} {title}\n"
                                f"💰 Было: {int(old_price)} ₸\n"
                                f"✅ Стало: {int(price)} ₸\n"
                                f"📊 Скидка: {diff} ₸ ({percent}%)"
                            ),
                            parse_mode="HTML"
                        )

                    if price <= target_price:
                        bot.send_message(
                            chat_id=user_id,
                            text=(
                                f"🎯 <b>ЦЕЛЬ ДОСТИГНУТА!</b>\n\n"
                                f"{emoji} {title}\n"
                                f"💰 Цена: {int(price)} ₸\n"
                                f"🎯 Цель: {int(target_price)} ₸\n\n"
                                f"👉 Самое время покупать!\n"
                                f"🔗 {url}"
                            ),
                            parse_mode="HTML"
                        )
            finally:
                scraper.close()

    print("✅ Автопроверка завершена")
def export_csv(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    items = get_all_items(user_id)
    if not items:
        update.message.reply_text("❌ Нет товаров", reply_markup=main_menu())
        return

    message = "📥 Выбери ID товара для экспорта:\n\n"
    for item in items:
        emoji_map = {"shop": "🛍️", "travel": "✈️", "realty": "🏠", "auto": "🚗"}
        emoji = emoji_map.get(item[2], "📦")
        message += f"{emoji} [{item[0]}] {item[3]}\n"

    message += "\nНапиши ID товара:"
    update.message.reply_text(message, reply_markup=main_menu())
    context.user_data["waiting_export_id"] = True
def main():
    init_db()

    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    # Обработчик добавления товара
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex("➕ Добавить товар"), add_item_start)],
        states={
            CATEGORY: [MessageHandler(Filters.text, get_category)],
            TITLE: [MessageHandler(Filters.text, get_title)],
            URL: [MessageHandler(Filters.text, get_url)],
            TARGET_PRICE: [MessageHandler(Filters.text, get_target_price)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(Filters.regex("❌ Отмена"), cancel)
        ]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("status", show_all_items))
    dp.add_handler(CommandHandler("check", check_prices))
    dp.add_handler(CommandHandler("report", daily_report))
    dp.add_handler(conv_handler)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("🤖 Бот запущен!")
    # Запускаем планировщик автопроверки
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        auto_check,
        'interval',
        hours=CHECK_INTERVAL,  # каждые 6 часов из config.py
        args=[updater.bot],
        id='auto_check',
        timezone=pytz.timezone('Asia/Almaty')

    )
    scheduler.start()
    print(f"⏰ Автопроверка каждые {CHECK_INTERVAL} часов")

    updater.start_polling()
    updater.idle()

    scheduler.shutdown()

if __name__ == "__main__":
    main()