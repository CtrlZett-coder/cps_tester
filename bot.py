import logging
import asyncio
import random
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.client.session.aiohttp import AiohttpSession # Импорт для прокси
from openai import OpenAI

# --- НАСТРОЙКИ ---
TOKEN = "8733664979:AAH8lQgeDFfsQcXENuPgh5AG4UzrXBYz7gU"
BASE_URL = "https://ctrlzett-coder.github.io/cps_tester/"
DEEPSEEK_KEY = "sk-b0241be117b0481e99ecb1446330f8f6"

# Настройка прокси для PythonAnywhere (обязательно для бесплатного тарифа)
# Это позволяет боту выходить в интернет через шлюз хостинга
proxy_url = "http://proxy.server:3128"
session = AiohttpSession(proxy=proxy_url)

# Инициализация логов
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота и диспетчера с использованием прокси-сессии
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

# Настройка клиента DeepSeek
client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

DEFAULT_INSULTS = [
    "Твоя мышка заснула, пока ты кликал?",
    "Это был замер скорости или тест на терпение?",
    "Моя бабушка кликает быстрее, когда ищет рассаду!",
    "Попробуй использовать пальцы, а не локоть."
]

async def get_ai_insult(cps):
    """Запрашивает подкол у DeepSeek с учетом настроения от CPS"""
    
    # Определяем "настроение" для нейросети
    if cps < 5:
        mood = "Жестко высмей этого нуба. Он кликает как сонная черепаха. Никакой пощады!"
    elif cps < 10:
        mood = "Слегка подстебни, но без лишней жестокости. Он старается, но до профи еще далеко."
    elif cps < 15:
        mood = "Вырази легкое удивление. Это уже неплохой результат, похвали и подколи одновременно."
    elif cps < 30:
        mood = "Ты в шоке! Ты не можешь поверить, что человек так быстро кликает мышкой. Это уровень профи!"
    else:
        mood = "ПОЛНЫЙ ВОСТОРГ! Это уровень бога кликов. Пиши самые лучшие и восхищенные комплименты, ты преклоняешься перед его мощью!"

    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            f"Ты — эмоциональный геймер-эксперт. {mood} "
                            "ПРАВИЛА: 1. КАТЕГОРИЧЕСКИ БЕЗ МАТА. "
                            "2. Пиши только про МЫШКУ и пальцы. "
                            "3. Ответ должен быть очень коротким (до 10 слов). "
                            "4. Отвечай на русском языке."
                        )
                    },
                    {"role": "user", "content": f"Мой результат: {cps} CPS."}
                ]
            )),
            timeout=8.0
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return random.choice(DEFAULT_INSULTS)

@dp.message(CommandStart())
async def start_command(message: types.Message):
    # ХАК ПРОТИВ КЭША: добавляем уникальный параметр к ссылке
    anticache = int(time.time())
    current_url = f"{BASE_URL}?v={anticache}"
    
    # Создаем кнопку Web App
    kb = [[types.KeyboardButton(
        text="🎮 ТРЕНИРОВАТЬ КЛИК", 
        web_app=types.WebAppInfo(url=current_url)
    )]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    # Возвращаем твой оригинальный текст
    await message.answer(
        f"Привет, {message.from_user.first_name}! 🔥\n\n"
        "Это профессиональный тестер CPS :)\n"
        "Проверь свою мышку на кликабельность! (если она конечно выживет XD)\n\n"
        "Жми кнопку внизу, чтобы начать замер (10 сек).",
        reply_markup=keyboard
    )

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        cps = float(data.get("cps", 0))
        total = int(data.get("total_clicks", 0))
        
        wait_msg = await message.answer("🤖 *AI анализирует твой позор...*", parse_mode="Markdown")
        
        insult = await get_ai_insult(cps)
        
        # Логика рангов
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
        await message.answer("⚠️ Ошибка. Твои клики слишком мощные для бота!")

async def main():
    print("--- БОТ ЗАПУЩЕН ---")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
