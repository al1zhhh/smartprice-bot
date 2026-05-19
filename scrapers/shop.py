# scrapers/shop.py
from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time


class KaspiShopScraper(BaseScraper):
    def get_price(self, url: str) -> float:
        try:
            self.driver.get(url)
            time.sleep(7)  # ждём дольше

            # Пробуем разные способы найти цену
            selectors = [
                (By.CLASS_NAME, "item__price-once"),
                (By.CSS_SELECTOR, ".item__price-once"),
                (By.XPATH, "//*[contains(@class, 'item__price-once')]"),
                (By.XPATH, "//*[contains(@class, 'price')]"),
            ]

            for by, selector in selectors:
                try:
                    elements = self.driver.find_elements(by, selector)
                    for el in elements:
                        text = el.text.strip()
                        if text:
                            print(f"   🔎 Найден текст: {text}")
                            digits = ''.join(filter(str.isdigit, text))
                            if digits and len(digits) >= 4:
                                return float(digits)
                except:
                    continue

            # Если ничего не нашли — выводим весь текст страницы для диагностики
            print("   ⚠️ Цена не найдена. Печатаем классы на странице...")
            elements = self.driver.find_elements(By.XPATH, "//*[@class]")
            classes = set()
            for el in elements[:50]:
                cls = el.get_attribute("class")
                if "price" in cls.lower():
                    classes.add(cls)
                    print(f"   📌 Класс с price: {cls} | Текст: {el.text[:30]}")

            return None

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return None