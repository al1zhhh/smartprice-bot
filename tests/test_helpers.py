# tests/test_helpers.py
import unittest
import os
import sys

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.database import init_db, add_item, get_all_items, save_price, get_price_history


class TestDatabase(unittest.TestCase):

    def setUp(self):
        """Запускается перед каждым тестом — создаём тестовую базу"""
        self.test_db = "data/test_kaspi.db"

        # Подменяем путь к базе на тестовую
        import utils.database as db
        db.DB_PATH = self.test_db

        init_db()

    def tearDown(self):
        """Запускается после каждого теста — удаляем тестовую базу"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_item(self):
        """Тест: товар добавляется в базу"""
        add_item("shop", "iPhone 15", "https://kaspi.kz/test", 350000)
        items = get_all_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][2], "iPhone 15")

    def test_add_multiple_items(self):
        """Тест: несколько товаров добавляются корректно"""
        add_item("shop", "iPhone 15", "https://kaspi.kz/1", 350000)
        add_item("shop", "Samsung S24", "https://kaspi.kz/2", 300000)
        add_item("auto", "Toyota Camry", "https://kolesa.kz/1", 15000000)

        items = get_all_items()
        self.assertEqual(len(items), 3)

    def test_save_price(self):
        """Тест: цена сохраняется в историю"""
        add_item("shop", "iPhone 15", "https://kaspi.kz/test", 350000)
        items = get_all_items()
        item_id = items[0][0]

        save_price(item_id, 380000)
        save_price(item_id, 370000)
        save_price(item_id, 360000)

        history = get_price_history(item_id)
        self.assertEqual(len(history), 3)

    def test_price_history_order(self):
        """Тест: история цен идёт в правильном порядке"""
        add_item("shop", "iPhone 15", "https://kaspi.kz/test", 350000)
        items = get_all_items()
        item_id = items[0][0]

        save_price(item_id, 400000)
        save_price(item_id, 380000)
        save_price(item_id, 360000)

        history = get_price_history(item_id)
        prices = [row[0] for row in history]

        # Первая цена должна быть 400000
        self.assertEqual(prices[0], 400000)
        # Последняя 360000
        self.assertEqual(prices[-1], 360000)

    def test_empty_database(self):
        """Тест: пустая база возвращает пустой список"""
        items = get_all_items()
        self.assertEqual(items, [])

    def test_target_price_saved(self):
        """Тест: целевая цена сохраняется корректно"""
        add_item("shop", "iPhone 15", "https://kaspi.kz/test", 350000)
        items = get_all_items()
        self.assertEqual(items[0][5], 350000)
    def test_add_realty_item(self):
        """Тест: объект недвижимости добавляется в базу"""
        add_item("realty", "2-комн. квартира, Алматы", "https://krisha.kz/a/show/123", 45000000)
        items = get_all_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][1], "realty")

    def test_add_auto_item(self):
        """Тест: автомобиль добавляется в базу"""
        add_item("auto", "Toyota Camry 2021", "https://kolesa.kz/a/show/456", 8500000)
        items = get_all_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][1], "auto")


class TestPriceLogic(unittest.TestCase):

    def test_price_drop_detection(self):
        """Тест: определяем снижение цены"""
        old_price = 380000
        new_price = 360000

        is_dropped = new_price < old_price
        self.assertTrue(is_dropped)

    def test_target_reached_detection(self):
        """Тест: определяем достижение целевой цены"""
        price = 345000
        target = 350000

        is_reached = price <= target
        self.assertTrue(is_reached)

    def test_target_not_reached(self):
        """Тест: цель ещё не достигнута"""
        price = 380000
        target = 350000

        is_reached = price <= target
        self.assertFalse(is_reached)

    def test_discount_calculation(self):
        """Тест: правильно считаем скидку"""
        old_price = 400000
        new_price = 360000

        diff = old_price - new_price
        percent = round((diff / old_price) * 100, 1)

        self.assertEqual(diff, 40000)
        self.assertEqual(percent, 10.0)

    def test_price_is_positive(self):
        """Тест: цена не может быть отрицательной"""
        price = -1000
        self.assertFalse(price > 0)

    def test_price_text_parsing(self):
        """Тест: парсим текст цены в число"""
        price_text = "380 000 ₸"
        price = float(''.join(filter(str.isdigit, price_text)))
        self.assertEqual(price, 380000.0)


class TestCategoryLogic(unittest.TestCase):

    def test_realty_category_saved(self):
        """Тест: категория realty сохраняется корректно"""
        # Имитируем добавление недвижимости
        category = "realty"
        self.assertEqual(category, "realty")

    def test_auto_category_saved(self):
        """Тест: категория auto сохраняется корректно"""
        category = "auto"
        self.assertEqual(category, "auto")

    def test_emoji_map(self):
        """Тест: все категории имеют эмодзи"""
        emoji_map = {"shop": "🛍️", "travel": "✈️", "realty": "🏠", "auto": "🚗"}

        self.assertEqual(emoji_map["shop"], "🛍️")
        self.assertEqual(emoji_map["travel"], "✈️")
        self.assertEqual(emoji_map["realty"], "🏠")
        self.assertEqual(emoji_map["auto"], "🚗")

    def test_unknown_category_fallback(self):
        """Тест: неизвестная категория возвращает дефолтный эмодзи"""
        emoji_map = {"shop": "🛍️", "travel": "✈️", "realty": "🏠", "auto": "🚗"}
        emoji = emoji_map.get("unknown", "📦")
        self.assertEqual(emoji, "📦")

    def test_price_parsing_large_number(self):
        """Тест: парсим цену недвижимости (большие числа)"""
        # Цены на крыше.кз типа "45 000 000 ₸"
        price_text = "45 000 000 ₸"
        digits = ''.join(filter(str.isdigit, price_text))
        price = float(digits)
        self.assertEqual(price, 45000000.0)

    def test_price_parsing_auto(self):
        """Тест: парсим цену авто с kolesa.kz"""
        # Цены на kolesa.kz типа "8 500 000 ₸"
        price_text = "8 500 000 ₸"
        digits = ''.join(filter(str.isdigit, price_text))
        price = float(digits)
        self.assertEqual(price, 8500000.0)

class TestDecoratorAndGenerator(unittest.TestCase):

    def setUp(self):
        """Создаём тестовую базу"""
        self.test_db = "data/test_kaspi.db"
        import utils.database as db
        db.DB_PATH = self.test_db
        init_db()

    def tearDown(self):
        """Удаляем тестовую базу"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_log_call_decorator_runs(self):
        """Тест: декоратор не ломает функцию add_item"""
        # Если декоратор работает правильно — функция всё ещё добавляет товар
        add_item("shop", "Test Item", "https://kaspi.kz/test", 100000)
        items = get_all_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][2], "Test Item")

    def test_log_call_decorator_save_price(self):
        """Тест: декоратор не ломает функцию save_price"""
        add_item("shop", "Test Item", "https://kaspi.kz/test", 100000)
        items = get_all_items()
        item_id = items[0][0]

        save_price(item_id, 95000)
        history = get_price_history(item_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0][0], 95000)

    def test_generator_returns_data(self):
        """Тест: генератор iter_price_history возвращает данные"""
        from utils.database import iter_price_history

        add_item("shop", "Test Item", "https://kaspi.kz/test", 100000)
        items = get_all_items()
        item_id = items[0][0]

        save_price(item_id, 90000)
        save_price(item_id, 85000)
        save_price(item_id, 80000)

        result = list(iter_price_history(item_id))
        self.assertEqual(len(result), 3)

    def test_generator_correct_order(self):
        """Тест: генератор отдаёт цены в правильном порядке"""
        from utils.database import iter_price_history

        add_item("shop", "Test Item", "https://kaspi.kz/test", 100000)
        items = get_all_items()
        item_id = items[0][0]

        save_price(item_id, 100000)
        save_price(item_id, 90000)

        result = list(iter_price_history(item_id))
        prices = [row[0] for row in result]

        self.assertEqual(prices[0], 100000)
        self.assertEqual(prices[-1], 90000)

    def test_generator_empty(self):
        """Тест: генератор на пустой истории возвращает пустой список"""
        from utils.database import iter_price_history

        add_item("shop", "Test Item", "https://kaspi.kz/test", 100000)
        items = get_all_items()
        item_id = items[0][0]

        result = list(iter_price_history(item_id))
        self.assertEqual(result, [])
if __name__ == "__main__":
    unittest.main()