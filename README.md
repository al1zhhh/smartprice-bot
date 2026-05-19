# 🏷️ SmartPrice Bot

A Telegram bot that tracks prices on Kazakh marketplaces and notifies users when prices drop to their target level.

## 📱 Demo

> Add your bot: [@SmartPriceBot](https://t.me/KaspiTrackerBot)

## ✨ Features

- 🛍️ **Kaspi.kz** — track product prices
- ✈️ **Aviata.kz** — track flight ticket prices
- 🏠 **Krisha.kz** — track real estate listings
- 🚗 **Kolesa.kz** — track car listings
- 📊 **Price history charts** — visualize price trends over time
- 🔔 **Telegram notifications** — instant alerts when price drops or target is reached
- 📥 **CSV export** — download price history as a spreadsheet
- ⏰ **Auto-check** — automatically checks prices every 6 hours
- 👥 **Multi-user** — each user tracks their own items independently

## 🗂️ Project Structure

```
smartprice-bot/
├── bot.py                  # Telegram bot — main entry point
├── config.py               # Configuration (reads from .env)
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── .env                    # Secret tokens (never commit this!)
├── .gitignore              # Git ignore rules
├── data/                   # SQLite database and generated charts
├── scrapers/
│   ├── base_scraper.py     # Base class with Selenium setup
│   ├── shop.py             # Kaspi Shop scraper
│   ├── travels.py          # Aviata scraper
│   ├── realty.py           # Krisha.kz scraper
│   └── auto.py             # Kolesa.kz scraper
├── utils/
│   ├── database.py         # SQLite database operations
│   ├── visualizer.py       # Price history charts (matplotlib)
│   └── notifier.py         # Telegram notification sender
└── tests/
    └── test_helpers.py     # 25 unit tests
```

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/smartprice-bot.git
cd smartprice-bot
```

### 2. Create a virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create `.env` file
Create a file named `.env` in the project root:
```
TELEGRAM_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

To get your token — talk to [@BotFather](https://t.me/BotFather) on Telegram.  
To get your chat ID — talk to [@userinfobot](https://t.me/userinfobot).

### 5. Install Chrome + ChromeDriver
The bot uses Selenium for web scraping. Make sure Google Chrome is installed.  
ChromeDriver is installed automatically via `webdriver-manager`.

## 🚀 Running the Bot

```bash
python bot.py
```

You should see:
```
✅ Database ready!
🤖 Bot started!
⏰ Auto-check every 6 hours
```

## 🧪 Running Tests

```bash
python -m unittest discover tests/
```

Expected output:
```
Ran 25 tests in 0.XXXs

OK
```

## 🤖 Bot Commands

| Command | Description |
|--------|-------------|
| `/start` | Open main menu |
| `/help` | Show help and commands |
| `/status` | View all tracked items |
| `/check` | Check all prices now |
| `/report` | View daily report |

## 📋 Bot Menu Buttons

| Button | Action |
|--------|--------|
| 📋 All Items | View all tracked items with current prices |
| ➕ Add Item | Add a new item to track |
| 🔍 Check Prices | Check all prices immediately |
| 🔎 Check One Item | Check price for a specific item |
| 📊 Charts | View price history chart |
| 🗑️ Delete Item | Remove an item from tracking |
| 📈 Report | View price change report |
| 📥 Export CSV | Download price history as CSV file |

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| Python 3.11 | Core language |
| python-telegram-bot | Telegram Bot API |
| Selenium | Web scraping |
| SQLite3 | Data storage |
| Matplotlib | Price charts |
| APScheduler | Scheduled auto-checks |
| python-dotenv | Secure token storage |

## 🏗️ Architecture

The project follows a modular architecture:

- **Scrapers** — each website has its own scraper class inheriting from `BaseScraper`
- **Utils** — reusable modules for database, visualization, and notifications
- **Bot** — handles all Telegram interactions and user conversations
- **Tests** — 25 unit tests covering database operations, price logic, and all categories

### Key Python Concepts Used
- **OOP & Inheritance** — `KaspiShopScraper`, `KrishaScraper`, `KolesaScraper` all inherit from `BaseScraper`
- **Decorator** — `@log_call` logs every database function call
- **Generator** — `iter_price_history()` yields price records one by one without loading all into memory
- **Exception handling** — all scrapers use try/except with specific error types
- **Context managers** — `with open(...)` for safe file operations

## 📊 Database Schema

```sql
tracked_items (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,        -- Telegram user ID
    category TEXT,          -- shop / travel / realty / auto
    title TEXT,
    url TEXT,
    current_price REAL,
    target_price REAL,
    created_at TIMESTAMP
)

price_history (
    id INTEGER PRIMARY KEY,
    item_id INTEGER,
    price REAL,
    checked_at TIMESTAMP
)
```

## 🔒 Security

- Bot tokens are stored in `.env` file, never hardcoded
- `.env` is listed in `.gitignore` — never pushed to GitHub
- Each user only sees their own tracked items

## 📄 License

MIT License — free to use and modify.

---

*Built with ❤️ as a university project at Astana IT University*
