# scrapers/base_scraper.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BaseScraper:
    def __init__(self):
        options = webdriver.ChromeOptions()

        options.add_argument("--headless=new")  # ← запуск без окна, стабильнее
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")  # ← нужно для headless на Windows
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(service=service, options=options)

        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru']});
            """
        })

        self.wait = WebDriverWait(self.driver, 15)
    def get_price(self, url: str) -> float:
        raise NotImplementedError

    def get_title(self, url: str) -> str:
        raise NotImplementedError

    def close(self):
        self.driver.quit()