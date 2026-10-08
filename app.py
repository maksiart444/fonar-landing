"""
Лендинг одного товара + приём заявок в Telegram.
Запуск: python app.py  → откроется на http://127.0.0.1:5000
"""
import csv
import os
import re
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

TG_RETRIES = 10       # сколько раз пытаться отправить заявку в Telegram
TG_RETRY_DELAY = 6    # пауза между попытками, сек

app = Flask(__name__)

# --- Настройки товара (меняешь здесь — меняется на всей странице) ---
PRODUCT = {
    "name": "Новорічний ліхтар зі снігопадом і музикою",
    "model": "XHF-8004",
    "sku": "56994",            # артикул в Dropt — чтобы быстро оформить заказ
    "price": 999,              # твоя цена продажи, грн
    "currency": "грн",
}

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
META_PIXEL_ID = os.getenv("META_PIXEL_ID", "")  # пусто = пиксель не подключается
# Демо-режим (по умолчанию включён): форма работает, но заявки никуда не уходят
# и не сохраняются. Для настоящих продаж — DEMO_MODE=0 в .env / на Render.
DEMO_MODE = os.getenv("DEMO_MODE", "1") != "0"

ORDERS_FILE = os.path.join(os.path.dirname(__file__), "orders.csv")
PHONE_RE = re.compile(r"^\+?380\d{9}$|^0\d{9}$")


def normalize_phone(raw: str) -> str:
    """Оставляет только цифры и плюс: '050 123-45-67' -> '0501234567'."""
    return re.sub(r"[^\d+]", "", raw or "")


def save_order(order: dict) -> None:
    """Запасная копия заявки в CSV — если Telegram вдруг не сработает."""
    is_new = not os.path.exists(ORDERS_FILE)
    with open(ORDERS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(order.keys()))
        if is_new:
            writer.writeheader()
        writer.writerow(order)


def send_to_telegram(order: dict) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не заданы в .env")
        return False
    text = (
        "🛒 НОВАЯ ЗАЯВКА\n\n"
        f"Товар: {PRODUCT['name']} ({PRODUCT['model']})\n"
        f"Артикул Dropt: {PRODUCT['sku']}\n"
        f"Кол-во: {order['qty']} шт.\n"
        f"Сумма: {order['total']} {PRODUCT['currency']}\n\n"
        f"Имя: {order['name']}\n"
        f"Телефон: {order['phone']}\n"
        f"Комментарий: {order['comment'] or '—'}\n\n"
        f"Время: {order['created_at']}"
    )
    for attempt in range(1, TG_RETRIES + 1):
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
                timeout=15,
            )
            if r.ok:
                print(f"[OK] Заявка отправлена в Telegram (попытка {attempt})")
                return True
            # Текст исключения не печатаем — в URL светится токен бота
            print(f"[!] Telegram ответил HTTP {r.status_code}, попытка {attempt}/{TG_RETRIES}")
        except requests.RequestException as e:
            print(f"[!] Нет связи с Telegram ({type(e).__name__}), попытка {attempt}/{TG_RETRIES}")
        if attempt < TG_RETRIES:
            time.sleep(TG_RETRY_DELAY)
    print("[!] Заявка НЕ отправлена в Telegram — смотри orders.csv")
    return False


@app.route("/")
def index():
    return render_template("index.html", p=PRODUCT, pixel_id=META_PIXEL_ID, demo=DEMO_MODE)


@app.route("/order", methods=["POST"])
def order():
    data = request.get_json(silent=True) or request.form

    # Ловушка для ботов: скрытое поле, человек его не заполняет
    if data.get("website"):
        return jsonify(ok=True)

    name = (data.get("name") or "").strip()[:60]
    phone = normalize_phone(data.get("phone"))
    comment = (data.get("comment") or "").strip()[:300]
    try:
        qty = max(1, min(int(data.get("qty", 1)), 10))
    except (TypeError, ValueError):
        qty = 1

    errors = {}
    if len(name) < 2:
        errors["name"] = "Вкажіть ім'я"
    if not PHONE_RE.match(phone):
        errors["phone"] = "Вкажіть телефон у форматі 0501234567"
    if errors:
        return jsonify(ok=False, errors=errors), 400

    if DEMO_MODE:
        return jsonify(ok=True, demo=True)

    order_data = {
        "created_at": datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%Y-%m-%d %H:%M"),
        "name": name,
        "phone": phone,
        "qty": qty,
        "total": qty * PRODUCT["price"],
        "comment": comment,
    }
    save_order(order_data)
    # Отправка в фоне — покупатель сразу получает ответ, не ждёт ретраев
    threading.Thread(target=send_to_telegram, args=(order_data,), daemon=True).start()
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(debug=True)
