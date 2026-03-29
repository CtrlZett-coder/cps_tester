import logging
import asyncio
import random
import time
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.utils.keyboard import InlineKeyboardBuilder
from openai import AsyncOpenAI

# --- НАСТРОЙКИ ---
TOKEN = "8733664979:AAH8lQgeDFfsQcXENuPgh5AG4UzrXBYz7gU"
BASE_URL = "https://ctrlzett-coder.github.io/cps_tester/"
DEEPSEEK_KEY = "sk-b0241be117b0481e99ecb1446330f8f6"

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = AsyncOpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

# --- СЛОВАРЬ ЯЗЫКОВ ООН ---
LANG_MAP = {
    "ru": {"name": "Русский 🇷🇺", "ai": "Russian", "btn": "🎮 ТРЕНИРОВАТЬ КЛИК", "wait": "🤖 *AI анализирует результат...*", "rank": ["Нубик 🐣", "Мастер 🦋", "Монстр 🐉", "КИБЕР-БОГ ⚡"]},
    "en": {"name": "English 🇺🇸", "ai": "English", "btn": "🎮 TRAIN CLICK", "wait": "🤖 *AI is analyzing...*", "rank": ["Noob 🐣", "Pro 🦋", "Monster 🐉", "CYBER GOD ⚡"]},
    "zh": {"name": "中文 🇨🇳", "ai": "Chinese", "btn": "🎮 点击训练", "wait": "🤖 *AI 正在分析...*", "rank": ["菜鸟 🐣", "高手 🦋", "怪物 🐉", "电竞之神 ⚡"]},
    "es": {"name": "Español 🇪🇸", "ai": "Spanish", "btn": "🎮 ENTRENAR CLIC", "wait": "🤖 *AI analizando...*", "rank": ["Novato 🐣", "Maestro 🦋", "Monstruo 🐉", "DIOS CIBERNÉTICO ⚡"]},
    "fr": {"name": "Français 🇫🇷", "ai": "French", "btn": "🎮 ENTRAÎNER LE CLIC", "wait": "🤖 *L'IA analyse...*", "rank": ["Débutant 🐣", "Maître 🦋", "Monstre 🐉", "DIEU DU CLIC ⚡"]},
    "ar": {"name": "العربية 🇸🇦", "ai": "Arabic", "btn": "🎮 تدريب النقر", "wait": "🤖 *الذكاء الاصطناعي يحلل...*", "rank": ["مبتدئ 🐣", "ماهر 🦋", "وحش 🐉", "إله النقرات ⚡"]}
}

async def get_ai_insult(cps, lang_code):
    lang_info = LANG_MAP.get(lang_code, LANG_MAP["en"])
    
    if cps < 5: mood = "Harshly mock this noob. Too slow."
    elif cps < 15: mood = "Light roast, he is trying but not enough."
    else: mood = "ABSOLUTE SHOCK! High speed, pure praise!"

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are an emotional pro-gamer. {mood} No profanity. Max 10 words. Respond ONLY in {lang_info['ai']}."
                },
                {"role": "user", "content": f"Result: {cps} CPS."}
            ],
            timeout=10.0
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return "Nice clicks!" if lang_code == "en" else "Хорошие клики!"

@dp.message(CommandStart())
async def start_command(message: types.Message):
    # Создаем выбор языка
    builder = InlineKeyboardBuilder()
    for code, info in LANG_MAP.items():
        builder.button(text=info["name"], callback_data=f"setlang_{code}")
    builder.adjust(2)
    
    await message.answer("Please choose your language / Пожалуйста, выберите язык:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("setlang_"))
async def set_language(callback: types.CallbackQuery):
    lang_code = callback.data.split("_")[1]
    lang_info = LANG_MAP[lang_code]
    
    anticache = int(time.time())
    # Передаем выбранный язык в Web App через URL (чтобы мини-апп тоже знал язык, если нужно)
    current_url = f"{BASE_URL}?v={anticache}&lang={lang_code}"
    
    kb = [[types.KeyboardButton(
        text=lang_info["btn"], 
        web_app=types.WebAppInfo(url=current_url)
    )]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    if lang_code == "ru":
        text = (f"Привет, {callback.from_user.first_name}! 🔥\n"
                "Это профессиональный тестер CPS :)\n"
                "Проверь свою мышку на кликабельность! (если она, конечно, выживет 🤣)\n\n"
                "Жми кнопку внизу! ⚡️🖱")
    else:
        text = f"Language set to {lang_info['name']}! Ready to test your speed? ⚡️"

    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        cps = float(data.get("cps", 0))
        total = int(data.get("total_clicks", 0))
        
        # Пытаемся определить язык из данных веб-аппа или по умолчанию ru
        lang_code = data.get("lang", "ru")
        lang_info = LANG_MAP.get(lang_code, LANG_MAP["ru"])
        
        wait_msg = await message.answer(lang_info["wait"], parse_mode="Markdown")
        insult = await get_ai_insult(cps, lang_code)
        
        ranks = lang_info["rank"]
        if cps < 8: rank = ranks[0]
        elif cps < 15: rank = ranks[1]
        elif cps < 22: rank = ranks[2]
        else: rank = ranks[3]

        # Локализация заголовков
        headers = {
            "ru": ("ИТОГИ ЗАМЕРА", "Скорость", "Всего кликов", "Ранг"),
            "en": ("TEST RESULTS", "Speed", "Total clicks", "Rank"),
            "zh": ("测试结果", "速度", "总点击次数", "等级"),
            "es": ("RESULTADOS", "Velocidad", "Clicks totales", "Rango"),
            "fr": ("RÉSULTATS", "Vitesse", "Total des clics", "Rang"),
            "ar": ("результаты", "سرعة", "إجمالي النقرات", "رتبة")
        }
        h = headers.get(lang_code, headers["en"])

        response = (
            f"🏁 **{h[0]}**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚀 {h[1]}: **{cps} CPS**\n"
            f"🎯 {h[2]}: **{total}**\n"
            f"🏆 {h[3]}: **{rank}**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💬 _{insult}_"
        )

        await wait_msg.delete()
        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Process Error: {e}")
        await message.answer("⚠️ Error processing data.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
