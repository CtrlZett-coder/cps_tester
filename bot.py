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
        "wait": "🤖 *AI анализирует твой позор...*",
        "ranks": ["Нубик 🐣", "Мастер 🦋", "Монстр 🐉", "КИБЕР-БОГ ⚡"],
        "headers": ["ИТОГИ ЗАМЕРА", "Скорость", "Всего кликов", "Ранг"]
    },
    "en": {
        "welcome": "Hello, {name}! 🔥\nProfessional CPS Tester :)\nCheck your mouse durability! (if it survives, haha 🤣)\n\nPress the button below! ⚡️🖱",
        "btn": "🎮 TRAIN CLICK",
        "change": "Language changed to English 🇺🇸",
        "wait": "🤖 *AI is analyzing your performance...*",
        "ranks": ["Noob 🐣", "Pro 🦋", "Monster 🐉", "CYBER GOD ⚡"],
        "headers": ["TEST RESULTS", "Speed", "Total Clicks", "Rank"]
    },
    "zh": {
        "welcome": "你好, {name}! 🔥\n专业 CPS 测试器 :)\n测试你的鼠标耐用性! (如果它能活下来 🤣)\n\n点击下方按钮! ⚡️🖱",
        "btn": "🎮 开始点击训练",
        "change": "语言已更改为 中文 🇨🇳",
        "wait": "🤖 *AI 正在分析你的表现...*",
        "ranks": ["菜鸟 🐣", "高手 🦋", "怪物 🐉", "电竞之神 ⚡"],
        "headers": ["测试结果", "速度", "总点击次数", "等级"]
    },
    "es": {
        "welcome": "¡Hola, {name}! 🔥\nProbador de CPS profesional :)\n¡Prueba la resistencia de tu ratón! (si sobrevive 🤣)\n\n¡Pulsa el botón! ⚡️🖱",
        "btn": "🎮 ENTRENAR CLIC",
        "change": "Idioma cambiado a Español 🇪🇸",
        "wait": "🤖 *AI analizando tu rendimiento...*",
        "ranks": ["Novato 🐣", "Maestro 🦋", "Monstruo 🐉", "DIOS CIBERNÉTICO ⚡"],
        "headers": ["RESULTADOS", "Velocidad", "Clicks totales", "Rango"]
    },
    "fr": {
        "welcome": "Bonjour, {name}! 🔥\nTesteur CPS professionnel :)\nTestez la survie de votre souris ! (si elle survit 🤣)\n\nAppuyez sur le bouton ! ⚡️🖱",
        "btn": "🎮 ENTRAÎNER LE CLIC",
        "change": "Langue changée en Français 🇫🇷",
        "wait": "🤖 *L'IA analyse votre performance...*",
        "ranks": ["Débutant 🐣", "Maître 🦋", "Monstre 🐉", "DIEU DU CLIC ⚡"],
        "headers": ["RÉSULTATS", "Vitesse", "Total clics", "Rang"]
    },
    "ar": {
        "welcome": "مرحباً {name}! 🔥\nمختبر CPS احترافي :)\nاختبر قوة الماوس الخاص بك! (إذا نجا 🤣)\n\nاضغط على الزر! ⚡️🖱",
        "btn": "🎮 تدريب النقر",
        "change": "تم تغيير اللغة إلى العربية 🇸🇦",
        "wait": "🤖 *الذكاء الاصطناعي يحلل مستواك...*",
        "ranks": ["مبتدئ 🐣", "ماهر 🦋", "وحش 🐉", "إله النقرات ⚡"],
        "headers": ["نتائج الاختبار", "سرعة", "إجمالي النقرات", "رتبة"]
    }
}

def get_lang_kb():
    builder = InlineKeyboardBuilder()
    flags = {"ru": "🇷🇺", "en": "🇺🇸", "zh": "🇨🇳", "es": "🇪🇸", "fr": "🇫🇷", "ar": "🇸🇦"}
    for code, flag in flags.items():
        builder.button(text=f"{code.upper()} {flag}", callback_data=f"lang_{code}")
    builder.adjust(2)
    return builder.as_markup()

async def get_ai_insult(cps, lang_code):
    """Генерация длинного и стильного ответа от AI"""
    if cps < 5:
        mood = "Жестко и длинно высмей этого нуба. Он кликает как улитка под транквилизаторами. Посоветуй ему сменить мышку на кирпич."
    elif cps < 12:
        mood = "Саркастично подмети, что это средний результат. Не ужасно, но и гордиться нечем. Упомяни, что бабушки в очереди кликают бодрее."
    elif cps < 20:
        mood = "Вырази уважение. Это уровень потного геймера. Спроси, не болят ли пальцы и какую смазку он использует для свитчей."
    else:
        mood = "ПОЛНЫЙ ВОСТОРГ И ШОК! Это уровень бога. Сравни его клики со скоростью света. Ты готов поклоняться его указательному пальцу."

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "system", 
                "content": (
                    f"Ты — харизматичный, дерзкий геймер-эксперт. {mood} "
                    "ПРАВИЛА: Категорически БЕЗ МАТА. Пиши развернуто (2-3 предложения). "
                    f"Отвечай ТОЛЬКО на языке: {lang_code}. Используй геймерский сленг."
                )
            },
            {"role": "user", "content": f"Мой результат: {cps} CPS."}],
            max_tokens=150, # Увеличили объем ответа
            timeout=12.0
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return "Неплохо, но моя микроволновка выдает больше CPS, когда я грею бутерброды!"

@dp.message(CommandStart())
@dp.message(Command("language"))
async def cmd_start(message: types.Message):
    await message.answer("🌐 Choose language / Выберите язык:", reply_markup=get_lang_kb())

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    L = LANG_DATA[lang]
    url = f"{BASE_URL}?v={int(time.time())}&lang={lang}"
    
    kb = [[types.KeyboardButton(text=L["btn"], web_app=types.WebAppInfo(url=url))]]
    await callback.message.answer(L["change"])
    await callback.message.answer(
        L["welcome"].format(name=callback.from_user.first_name), 
        reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
    await callback.answer()

@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
    try:
        raw_data = json.loads(message.web_app_data.data)
        cps = float(raw_data.get("cps", 0))
        total = raw_data.get("total_clicks", 0)
        lang = raw_data.get("lang", "ru")
        
        L = LANG_DATA.get(lang, LANG_DATA["en"])
        
        wait = await message.answer(L["wait"], parse_mode="Markdown")
        
        # Получаем развернутый ответ от AI
        insult = await get_ai_insult(cps, lang)
        
        r_idx = 0 if cps < 8 else 1 if cps < 15 else 2 if cps < 22 else 3
        rank = L["ranks"][r_idx]
        h = L["headers"]

        res = (
            f"🏁 **{h[0]}**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚀 {h[1]}: **{cps} CPS**\n"
            f"🎯 {h[2]}: **{total}**\n"
            f"🏆 {h[3]}: **{rank}**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💬 {insult}" # Без курсива, так как текста много
        )
        
        await wait.delete()
        await message.answer(res, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Handle Data Error: {e}")
        await message.answer("❌ Ошибка при обработке твоих кликов. Видимо, они слишком быстрые для интернета!")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
