# scrapers/travels.py
from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time


class TravelsScraper(BaseScraper):

    def get_price(self, url: str) -> float:
        """Получить минимальную цену билета"""
        try:
            self.driver.get(url)
            time.sleep(8)  # ждём загрузки билетов

            # Ищем ВСЕ элементы с ценой
            price_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "strong.text-base.font-bold"
            )

            if not price_elements:
                print("   ⚠️ Элементы с ценой не найдены")
                return None

            # Собираем все цены и берём минимальную
            prices = []
            for el in price_elements:
                text = el.text.strip()
                print(f"   🔎 Найден текст: {text}")
                digits = ''.join(filter(str.isdigit, text))
                if digits:
                    prices.append(float(digits))

            if not prices:
                return None

            # Возвращаем минимальную цену
            return min(prices)

        except Exception as e:
            print(f"❌ Ошибка при получении цены: {e}")
            return None

    def get_title(self, url: str) -> str:
        return "Авиабилет"