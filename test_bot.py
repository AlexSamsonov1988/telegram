from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import urllib.parse
import requests
from bs4 import BeautifulSoup
import random

TOKEN = "7753353202:AAEBbxRkECAO0PVKRYYo1s_DKKEQJOP0UNk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот.\n"
        "• /music <название> — поиск трека на Яндекс.Музыке\n"
        "• /qobuz <название> — поиск трека на Qobuz\n"
        "• Напиши 'анекдот', 'армянское радио' или 'шутка' — расскажу анекдот!"
    )

async def music_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text(
            "Напиши после /music название исполнителя или песни, например:\n/music Imagine Dragons Believer"
        )
        return
    url_query = urllib.parse.quote(query)
    yandex_search_url = f"https://music.yandex.ru/search?text={url_query}"
    await update.message.reply_text(f"Вот ссылка на поиск Яндекс Музыки по запросу:\n{yandex_search_url}")

# ----------- Qobuz Search -----------
def search_qobuz_tracks(query, app_id="269645017"):
    url = "https://www.qobuz.com/api.json/0.2/search"
    params = {
        "query": query,
        "type": "tracks",
        "app_id": app_id
    }
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
    reply = ""
    for t in tracks[:3]:
        title = t.get('title')
        artist = t.get('artist', {}).get('name', '')
        url = f"https://www.qobuz.com{t.get('url', '')}" if t.get('url') else ""
        reply += f"🎵 {title} — {artist}\nСсылка: {url}\n\n"
    await update.message.reply_text(reply or "Ошибка обработки треков.")

# ----------- Anecdotes -----------
def get_joke_from_anekdotru():
    url = "https://www.anekdot.ru/random/anekdot/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers, timeout=7)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        jokes = [div.get_text(strip=True) for div in soup.find_all("div", class_="text")]
        if jokes:
            return random.choice(jokes)
        else:
            return "Сегодня нет анекдотов, попробуй чуть позже!"
    except Exception as e:
        print("Ошибка:", e)
        return f"Не удалось получить анекдот с сайта anekdot.ru. Причина: {e}"

def get_armyanskoe_radio_joke():
    url = "https://www.anekdot.ru/tags/%D0%B0%D1%80%D0%BC%D1%8F%D0%BD%D1%81%D0%BA%D0%BE%D0%B5%20%D1%80%D0%B0%D0%B4%D0%B8%D0%BE/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers, timeout=7)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        jokes = [div.get_text(strip=True) for div in soup.find_all("div", class_="text")]
        if jokes:
            return random.choice(jokes)
        else:
            return "Нет свежих шуток про армянское радио."
    except Exception as e:
        print("Ошибка:", e)
        return f"Не удалось получить шутку про армянское радио. Причина: {e}"

async def reply_to_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "армянское радио" in text:
        joke = get_armyanskoe_radio_joke()
        await update.message.reply_text(joke)
    elif any(word in text for word in ["анекдот", "шутка"]):
        joke = get_joke_from_anekdotru()
        await update.message.reply_text(joke)
    else:
        await update.message.reply_text(f"Ты написал: {update.message.text}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("music", music_command))
    app.add_handler(CommandHandler("qobuz", qobuz_command))  # Новая команда!
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_text))
    app.run_polling()

if __name__ == "__main__":
    main()
