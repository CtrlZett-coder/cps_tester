import logging
import asyncio
import random
import time
import json  # ДОБАВЛЕНО
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.client.session.aiohttp import AiohttpSession
from openai import AsyncOpenAI  # ИСПОЛЬЗУЕМ АСИНХРОННЫЙ КЛИЕНТ

# --- НАСТРОЙКИ ---
TOKEN = "8733664979:AAH8lQgeDFfsQcXENuPgh5AG4UzrXBYz7gU"
BASE_URL = "https://ctrlzett-coder.github.io/cps_tester/"
DEEPSEEK_KEY = "sk-b0241be117b0481e99ecb1446330f8f6"

# Настройка прокси (Раскомментируй ТОЛЬКО для PythonAnywhere)
# proxy_url = "http://proxy.server:3128"
# session = AiohttpSession(proxy=proxy_url)
# bot = Bot(token=TOKEN, session=session)

bot = Bot(token=TOKEN) # Для локального теста без прокси
dp = Dispatcher()

# Асинхронный клиент DeepSeek
client = AsyncOpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

DEFAULT_INSULTS = [
    "Твоя мышка заснула, пока ты кликал?",
    "Это был замер скорости или тест на терпение?",
    "Моя бабушка кликает быстрее!",
    "Попробуй использовать пальцы, а не локоть."
]

async def get_ai_insult(cps):
    if cps < 5: mood = "Жестко высмей этого нуба. Он сонная черепаха."
    elif cps < 10: mood = "Слегка подстебни, он старается, но слабо."
    elif cps < 15: mood = "Похвали и подколи одновременно. Хороший результат."
    else: mood = "ПОЛНЫЙ ВОСТОРГ! Это уровень бога кликов!"

    try:
        # Теперь используем await напрямую с асинхронным клиентом
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system", 
                    "content": f"Ты — эмоциональный геймер. {mood} Без мата. До 10 слов. На русском."
                },
                {"role": "user", "content": f"Результат: {cps} CPS."}
            ],
            timeout=10.0
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return random.choice(DEFAULT_INSULTS)

@dp.message(CommandStart())
async def start_command(message: types.Message):
    anticache = int(time.time())
    current_url = f"{BASE_URL}?v={anticache}"
    
    kb = [[types.KeyboardButton(
        text="🎮 ТРЕНИРОВАТЬ КЛИК", 
        web_app=types.WebAppInfo(url=current_url)
    )]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 🔥\n"
        "Проверь свою мышку на кликабельность! (если она, конечно, выживет 🤣)\n\n"
        "Жми кнопку внизу! ⚡️🖱",
        reply_markup=keyboard
    )

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        # Теперь json импортирован и ошибки не будет
        data = json.loads(message.web_app_data.data)
        cps = float(data.get("cps", 0))
        total = int(data.get("total_clicks", 0))
        
        wait_msg = await message.answer("🤖 *AI анализирует результат...*", parse_mode="Markdown")
        
        insult = await get_ai_insult(cps)
        
        if cps < 8: rank = "Нубик 🐣"
        elif cps < 15: rank = "Butterfly-мастер 🦋"
        elif cps < 22: rank = "Drag-click Монстр 🐉"
        else: rank = "КИБЕР-БОГ ⚡"

        response = (
            f"🏁 **ИТОГИ ЗАМЕРА**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚀 Скорость: **{cps} CPS**\n"
            f"🎯 Всего кликов: **{total}**\n"
            f"🏆 Ранг: **{rank}**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💬 _{insult}_"
        )

        await wait_msg.delete()
        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Process Error: {e}")
        await message.answer("⚠️ Ошибка обработки данных.")

async def main():
    logging.info("Бот запущен")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
