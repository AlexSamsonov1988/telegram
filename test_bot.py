import os
import urllib.parse
import random
import requests
from bs4 import BeautifulSoup

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters


TOKEN = os.getenv("BOT_TOKEN")  # берем токен из окружения (.env через systemd EnvironmentFile)

# ---------- Меню ----------
def main_menu():
    keyboard = [
        [KeyboardButton("🎵 Музыка"), KeyboardButton("🎧 Qobuz")],
        [KeyboardButton("😂 Анекдот"), KeyboardButton("📻 Армянское радио")],
        [KeyboardButton("ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


HELP_TEXT = (
    "Команды и возможности:\n"
    "• /music <название> — ссылка на поиск в Яндекс.Музыке\n"
    "• /qobuz <название> — поиск трека в Qobuz (топ-3)\n"
    "• Напиши: 'анекдот' / 'шутка' — случайный анекдот\n"
    "• Напиши: 'армянское радио' — шутка из тега\n"
    "\n"
    "Можно пользоваться кнопками меню 👇"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Выбери действие 👇", reply_markup=main_menu())
    await update.message.reply_text(HELP_TEXT)


# ---------- Яндекс.Музыка (ссылка) ----------
async def music_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text(
            "Напиши после /music название исполнителя или песни, например:\n"
            "/music Imagine Dragons Believer"
        )
        return

    url_query = urllib.parse.quote(query)
    yandex_search_url = f"https://music.yandex.ru/search?text={url_query}"
    await update.message.reply_text(f"Вот ссылка на поиск Яндекс Музыки:\n{yandex_search_url}")


# ---------- Qobuz ----------
def search_qobuz_tracks(query, app_id="269645017"):
    url = "https://www.qobuz.com/api.json/0.2/search"
    params = {"query": query, "type": "tracks", "app_id": app_id}
    try:
        resp = requests.get(url, params=params, timeout=7)
        resp.raise_for_status()
        data = resp.json()
        return data.get("tracks", {}).get("items", [])
    except Exception as e:
        print("Ошибка Qobuz API:", e)
        return []

async def qobuz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Напиши после /qobuz название исполнителя или песни.")
        return

    tracks = search_qobuz_tracks(query)
    if not tracks:
        await update.message.reply_text("Не нашёл ничего в Qobuz.")
        return

    reply_lines = []
    for t in tracks[:3]:
        title = t.get("title", "")
        artist = t.get("artist", {}).get("name", "")
        url = f"https://www.qobuz.com{t.get('url', '')}" if t.get("url") else ""
        reply_lines.append(f"🎵 {title} — {artist}\nСсылка: {url}")

    await update.message.reply_text("\n\n".join(reply_lines))


# ---------- Анекдоты ----------
def get_joke_from_anekdotru():
    url = "https://www.anekdot.ru/random/anekdot/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=7)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        jokes = [div.get_text(strip=True) for div in soup.find_all("div", class_="text")]
        return random.choice(jokes) if jokes else "Сегодня нет анекдотов, попробуй чуть позже!"
    except Exception as e:
        print("Ошибка:", e)
        return f"Не удалось получить анекдот. Причина: {e}"

def get_armyanskoe_radio_joke():
    url = "https://www.anekdot.ru/tags/%D0%B0%D1%80%D0%BC%D1%8F%D0%BD%D1%81%D0%BA%D0%BE%D0%B5%20%D1%80%D0%B0%D0%B4%D0%B8%D0%BE/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=7)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        jokes = [div.get_text(strip=True) for div in soup.find_all("div", class_="text")]
        return random.choice(jokes) if jokes else "Нет свежих шуток про армянское радио."
    except Exception as e:
        print("Ошибка:", e)
        return f"Не удалось получить шутку про армянское радио. Причина: {e}"


# ---------- Текстовые сообщения и кнопки ----------
async def reply_to_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_raw = update.message.text
    text = text_raw.lower()

    # кнопки меню
    if "музыка" in text and text_raw.startswith("🎵"):
        await update.message.reply_text("Ок. Напиши запрос так:\n/music <исполнитель или трек>")
        return

    if "qobuz" in text and text_raw.startswith("🎧"):
        await update.message.reply_text("Ок. Напиши запрос так:\n/qobuz <исполнитель или трек>")
        return

    if "анекдот" in text or text_raw.startswith("😂"):
        await update.message.reply_text(get_joke_from_anekdotru())
        return

    if "армянское радио" in text or text_raw.startswith("📻"):
        await update.message.reply_text(get_armyanskoe_radio_joke())
        return

    if "помощь" in text or text_raw.startswith("ℹ️"):
        await update.message.reply_text(HELP_TEXT)
        return

    # остальное
    if "армянское радио" in text:
        await update.message.reply_text(get_armyanskoe_radio_joke())
    elif any(word in text for word in ["анекдот", "шутка"]):
        await update.message.reply_text(get_joke_from_anekdotru())
    else:
        await update.message.reply_text("Не понял. Нажми кнопку меню или напиши /start.")


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не задан. Проверь .env и systemd EnvironmentFile.")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("music", music_command))
    app.add_handler(CommandHandler("qobuz", qobuz_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_text))
    app.run_polling()


if __name__ == "__main__":
    main()

