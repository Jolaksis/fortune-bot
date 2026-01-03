import asyncio
import random
import json
import os
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "data.json"
PREDICTIONS_JSON = "predictions.json"
MAX_USERS = 100

bot = Bot(token=TOKEN)
dp = Dispatcher()

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔮 Получить предсказание")]],
    resize_keyboard=True
)

def find_pdf():
    for f in os.listdir("."):
        if f.lower().endswith(".pdf"):
            return f
    return None

def extract_predictions(pdf_path):
    from PyPDF2 import PdfReader
    reader = PdfReader(pdf_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    pattern = re.compile(r'\d+\.\s*(.+?)(?=\n\d+\.|$)', re.S)
    return [re.sub(r'\s+', ' ', p).strip() for p in pattern.findall(text)]

def load_predictions():
    if os.path.exists(PREDICTIONS_JSON):
        with open(PREDICTIONS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)

    pdf = find_pdf()
    preds = extract_predictions(pdf)[:MAX_USERS]

    with open(PREDICTIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(preds, f, ensure_ascii=False, indent=4)

    return preds

predictions = load_predictions()

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"users": {}, "free_predictions": predictions.copy()}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def remaining():
    return len(data["free_predictions"])

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🔮 Добро пожаловать!\n\n"
        f"📊 Осталось предсказаний: {remaining()} из {MAX_USERS}",
        reply_markup=keyboard
    )

@dp.message(lambda m: m.text == "🔮 Получить предсказание")
async def get_prediction(message: types.Message):
    user_id = str(message.from_user.id)

    if user_id in data["users"]:
        await message.answer(
            f"🔮 *{data['users'][user_id]}*",
            parse_mode="Markdown"
        )
        return

    if not data["free_predictions"]:
        await message.answer("🚫 Все предсказания уже выданы 😔")
        return

    prediction = random.choice(data["free_predictions"])
    data["free_predictions"].remove(prediction)
    data["users"][user_id] = prediction
    save_data()

    await message.answer(
        f"✨ *{prediction}*\n\n📊 Осталось: {remaining()}",
        parse_mode="Markdown"
    )

async def main():
    print("🤖 Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
