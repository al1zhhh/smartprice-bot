# scrapers/auto.py
from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
import time
import re


class KolesaScraper(BaseScraper):
    """Скрапер для kolesa.kz — объявления об автомобилях"""

    def get_price(self, url: str) -> float:
        try:
            self.driver.get(url)
            time.sleep(6)

            # Точные селекторы заголовка цены на kolesa.kz
            selectors = [
                (By.CSS_SELECTOR, "div.offer-price .price"),
                (By.CSS_SELECTOR, ".offer-price__cost"),
                (By.CSS_SELECTOR, "span.price"),
                (By.XPATH, "//span[contains(@class,'price') and not(contains(@class,'old'))]"),
                (By.XPATH, "//div[contains(@class,'offer-price')]//span"),
            ]

            for by, selector in selectors:
                try:
                    elements = self.driver.find_elements(by, selector)
                    for el in elements:
                        text = el.text.strip()
                        if not text:
                            continue
                        print(f"   🔎 Найден текст: {text}")

                        # Убираем всё кроме цифр и пробелов
                        # "50 000 000 ₸" → "50000000"
                        clean = re.sub(r'[^\d\s]', '', text).replace(' ', '')
                        if clean and len(clean) >= 6:
                            price = float(clean)
                            # Цена авто от 500 000 до 500 000 000
                            if 500_000 <= price <= 500_000_000:
                                return price
                except:
                    continue

            # Попробуем через page_source напрямую
            print("   ⚠️ Пробуем через page_source...")
            source = self.driver.page_source
            # Ищем паттерн цены: число от 6 до 9 цифр перед ₸ или тг
            matches = re.findall(r'(\d[\d\s]{4,})\s*[₸т]', source)
            for match in matches:
                clean = match.replace(' ', '')
                if clean and len(clean) >= 6:
                    price = float(clean)
                    if 500_000 <= price <= 500_000_000:
                        print(f"   ✅ Найдено через source: {price}")
                        return price

            # Диагностика
            print("   ⚠️ Цена не найдена. Ищем классы с 'price'...")
            elements = self.driver.find_elements(By.XPATH, "//*[@class]")
            for el in elements[:80]:
                cls = el.get_attribute("class")
                if cls and "price" in cls.lower():
                    print(f"   📌 Класс: {cls} | Текст: {el.text[:40]}")

            return None

        except Exception as e:
            print(f"❌ Ошибка kolesa: {e}")
            return None

    def get_title(self, url: str) -> str:
        return "Автомобиль (kolesa.kz)"