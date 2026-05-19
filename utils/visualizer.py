# utils/visualizer.py
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from utils.database import get_price_history, get_all_items, iter_price_history

def plot_price_history(item_id: int):
    """График динамики цен для одного товара"""

    # Получаем данные из базы
    from utils.database import get_price_history, iter_price_history

    history = list(iter_price_history(item_id))
    if not history:
        print("❌ Нет данных для графика")
        return

    if len(history) < 2:
        print("⚠️ Нужно минимум 2 записи для графика. Запусти программу ещё раз позже.")
        return

    # Разбиваем на цены и даты
    prices = [row[0] for row in history]
    dates = [datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") for row in history]

    # Получаем инфо о товаре
    items = get_all_items()
    item = next((i for i in items if i[0] == item_id), None)
    title = item[2] if item else "Товар"
    target_price = item[5] if item else None

    # Создаём график
    fig, ax = plt.subplots(figsize=(12, 6))

    # Линия цены
    ax.plot(dates, prices,
            color="#FF6B00",  # оранжевый как Kaspi
            linewidth=2.5,
            marker="o",
            markersize=8,
            label="Цена")

    # Линия целевой цены
    if target_price:
        ax.axhline(y=target_price,
                   color="green",
                   linestyle="--",
                   linewidth=2,
                   label=f"Целевая цена: {int(target_price)} ₸")

    # Закрашиваем область между ценой и целью
    ax.fill_between(dates, prices, target_price,
                    where=[p > target_price for p in prices],
                    alpha=0.1, color="red",
                    label="Выше цели")
    ax.fill_between(dates, prices, target_price,
                    where=[p <= target_price for p in prices],
                    alpha=0.1, color="green",
                    label="Цель достигнута!")

    # Подписи на точках
    for date, price in zip(dates, prices):
        ax.annotate(f"{int(price)} ₸",
                    xy=(date, price),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha="center",
                    fontsize=9)

    # Форматирование
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
    plt.xticks(rotation=45)

    ax.set_title(f"📈 История цен: {title}", fontsize=14, fontweight="bold")
    ax.set_xlabel("Дата", fontsize=12)
    ax.set_ylabel("Цена (₸)", fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Минимальная и максимальная цена
    ax.annotate(f"Мин: {int(min(prices))} ₸",
                xy=(dates[prices.index(min(prices))], min(prices)),
                xytext=(0, -20),
                textcoords="offset points",
                ha="center",
                color="green",
                fontsize=9,
                fontweight="bold")

    plt.tight_layout()

    # Сохраняем
    filename = f"data/price_chart_{item_id}.png"
    plt.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"✅ График сохранён: {filename}")
    plt.show()


def plot_all_items():
    """График всех отслеживаемых товаров"""
    items = get_all_items()

    if not items:
        print("❌ Нет товаров для графика")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ["#FF6B00", "#0066CC", "#00AA44", "#CC0000", "#9900CC"]

    for i, item in enumerate(items):
        item_id = item[0]
        title = item[2]
        history = get_price_history(item_id)

        if len(history) < 2:
            continue

        prices = [row[0] for row in history]
        dates = [datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") for row in history]

        color = colors[i % len(colors)]
        ax.plot(dates, prices,
                color=color,
                linewidth=2,
                marker="o",
                markersize=6,
                label=title)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
    plt.xticks(rotation=45)

    # Было
    ax.set_title(f"📈 История цен: {title}", fontsize=14, fontweight="bold")

    # Стало
    ax.set_title(f"История цен: {title}", fontsize=14, fontweight="bold")
    ax.set_xlabel("Дата", fontsize=12)
    ax.set_ylabel("Цена (₸)", fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("data/all_items_chart.png", dpi=150, bbox_inches="tight")
    print("✅ График сохранён: data/all_items_chart.png")
    plt.show()