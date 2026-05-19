# utils/database.py
import sqlite3
import os
import csv
from config import DB_PATH


def log_call(func):
    """Декоратор: логирует вызов каждой функции базы данных"""
    def wrapper(*args, **kwargs):
        print(f"[DB] Вызов: {func.__name__}")
        result = func(*args, **kwargs)
        print(f"[DB] Готово: {func.__name__}")
        return result
    return wrapper


def get_connection():
    """Подключение к базе данных"""
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """Создание таблиц при первом запуске"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracked_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            current_price REAL,
            target_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            price REAL NOT NULL,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES tracked_items(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ База данных готова!")


@log_call
def add_item(user_id, category, title, url, target_price):
    """Добавить новый товар для отслеживания"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tracked_items (user_id, category, title, url, target_price)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, category, title, url, target_price))
    conn.commit()
    conn.close()
    print(f"✅ Добавлено: {title}")


def get_all_items(user_id=None):
    """Получить товары — если user_id указан, только его товары"""
    conn = get_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute("SELECT * FROM tracked_items WHERE user_id = ?", (user_id,))
    else:
        cursor.execute("SELECT * FROM tracked_items")

    items = cursor.fetchall()
    conn.close()
    return items


@log_call
def save_price(item_id, price):
    """Сохранить новую цену в историю"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO price_history (item_id, price)
        VALUES (?, ?)
    """, (item_id, price))

    cursor.execute("""
        UPDATE tracked_items SET current_price = ?
        WHERE id = ?
    """, (price, item_id))

    conn.commit()
    conn.close()


def get_price_history(item_id):
    """Получить историю цен товара"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT price, checked_at FROM price_history
        WHERE item_id = ?
        ORDER BY checked_at ASC
    """, (item_id,))
    history = cursor.fetchall()
    conn.close()
    return history


def iter_price_history(item_id):
    """Генератор: отдаёт историю цен по одной записи"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT price, checked_at FROM price_history
        WHERE item_id = ?
        ORDER BY checked_at ASC
    """, (item_id,))
    for row in cursor:
        yield row
    conn.close()


def export_to_csv(item_id: int, filepath: str):
    """Экспортирует историю цен товара в CSV файл"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT title FROM tracked_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    title = row[0]

    cursor.execute("""
        SELECT price, checked_at FROM price_history
        WHERE item_id = ?
        ORDER BY checked_at ASC
    """, (item_id,))
    history = cursor.fetchall()
    conn.close()

    if not history:
        return None

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Товар', 'Цена (₸)', 'Дата проверки'])
        for price, checked_at in history:
            writer.writerow([title, int(price), checked_at])

    return filepath


def get_all_users():
    """Получить всех уникальных пользователей"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM tracked_items")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users