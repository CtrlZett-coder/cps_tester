import logging
import asyncio
import random
import time
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from openai import AsyncOpenAI

# --- НАСТРОЙКИ ---
TOKEN = "8733664979:AAH8lQgeDFfsQcXENuPgh5AG4UzrXBYz7gU"
BASE_URL = "https://ctrlzett-coder.github.io/cps_tester/"
DEEPSEEK_KEY = "sk-b0241be117b0481e99ecb1446330f8f6"

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = AsyncOpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

# --- СЛОВАРЬ ПЕРЕВОДОВ ---
LANG_DATA = {
    "ru": {
        "welcome": "Привет, {name}! 🔥\nЭто профессиональный тестер CPS :)\nПроверь свою мышку на кликабельность! (если она, конечно, выживет 🤣)\n\nЖми кнопку внизу! ⚡️🖱",
        "btn": "🎮 ТРЕНИРОВАТЬ КЛИК",
        "change": "Язык изменен на Русский 🇷🇺",
        "ai_lang": "Russian"
    },
    "en": {
        "welcome": "Hello, {name}! 🔥\nThis is a professional CPS tester :)\nTest your mouse for clickability! (if it survives, of course 🤣)\n\nPress the button below! ⚡️🖱",
        "btn": "🎮 TRAIN CLICK",
        "change": "Language changed to English 🇺🇸",
        "ai_lang": "English"
    },
    "zh": {
        "welcome": "你好, {name}! 🔥\n这是专业的 CPS 测试器 :)\n测试你的鼠标点击能力! (如果它能幸存下来 🤣)\n\n点击下方按钮开始! ⚡️🖱",
        "btn": "🎮 开始点击训练",
        "change": "语言已更改为 中文 🇨🇳",
        "ai_lang": "Chinese"
    },
    "es": {
        "welcome": "¡Hola, {name}! 🔥\nEste es un probador de CPS profesional :)\n¡Prueba la clicabilidad de tu ratón! (si sobrevive, por supuesto 🤣)\n\n¡Pulsa el botón de abajo! ⚡️🖱",
        "btn": "🎮 ENTRENAR CLIC",
        "change": "Idioma cambiado a Español 🇪🇸",
        "ai_lang": "Spanish"
    },
    "fr": {
        "welcome": "Bonjour, {name}! 🔥\nCeci est un testeur CPS professionnel :)\nTestez la cliquabilité de votre souris ! (si elle survit, bien sûr 🤣)\n\nAppuyez sur le bouton ci-dessous ! ⚡️🖱",
        "btn": "🎮 ENTRAÎNER LE CLIC",
        "change": "Langue changée en Français 🇫🇷",
        "ai_lang": "French"
    },
    "ar": {
        "welcome": "مرحباً {name}! 🔥\nهذا اختبار CPS احترافي :)\nاختبر قدرة الماوس على النقر! (إذا نجا بالطبع 🤣)\n\nاضغط على الزر أدناه! ⚡️🖱",
        "btn": "🎮 تدريب النقر",
        "change": "تم تغيير اللغة إلى العربية 🇸🇦",
        "ai_lang": "Arabic"
    }
}

def get_lang_keyboard():
    builder = InlineKeyboardBuilder()
    for code in LANG_DATA.keys():
        flag = "🇷🇺" if code=="ru" else "🇺🇸" if code=="en" else "🇨🇳" if code=="zh" else "🇪🇸" if code=="es" else "🇫🇷" if code=="fr" else "🇸🇦"
        builder.button(text=f"{code.upper()} {flag}", callback_data=f"lang_{code}")
    builder.adjust(2)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Please choose your language / Выберите язык:", reply_markup=get_lang_keyboard())

@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    await message.answer("🌐 Choose language / Выберите язык:", reply_markup=get_lang_keyboard())

@dp.callback_query(F.data.startswith("lang_"))
async def callbacks_lang(callback: types.CallbackQuery):
    lang_code = callback.data.split("_")[1]
    data = LANG_DATA[lang_code]
    
    # Ссылка с параметром языка для HTML
    url = f"{BASE_URL}?v={int(time.time())}&lang={lang_code}"
    
    kb = [[types.KeyboardButton(text=data["btn"], web_app=types.WebAppInfo(url=url))]]
    reply_markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await callback.message.answer(data["change"])
    await callback.message.answer(data["welcome"].format(name=callback.from_user.first_name), reply_markup=reply_markup)
    await callback.answer()

# (Оставь остальной код handle_webapp_data и main из предыдущего ответа)
