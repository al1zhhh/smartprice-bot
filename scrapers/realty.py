# scrapers/realty.py
from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
import time


class KrishaScraper(BaseScraper):
    """Скрапер для krisha.kz — объявления о недвижимости"""

    def get_price(self, url: str) -> float:
        try:
            self.driver.get(url)
            time.sleep(6)

            selectors = [
                (By.CLASS_NAME, "offer__price"),
                (By.CSS_SELECTOR, ".offer__price"),
                (By.CSS_SELECTOR, "[data-name='price']"),
                (By.XPATH, "//*[contains(@class, 'offer__price')]"),
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
                            if digits and len(digits) >= 5:
                                return float(digits)
                except:
                    continue

            # Диагностика если не нашли
            print("   ⚠️ Цена не найдена. Ищем классы с 'price'...")
            elements = self.driver.find_elements(By.XPATH, "//*[@class]")
            for el in elements[:80]:
                cls = el.get_attribute("class")
                if cls and "price" in cls.lower():
                    print(f"   📌 Класс: {cls} | Текст: {el.text[:40]}")

            return None

        except Exception as e:
            print(f"❌ Ошибка krisha: {e}")
            return None

    def get_title(self, url: str) -> str:
        return "Недвижимость (krisha.kz)"