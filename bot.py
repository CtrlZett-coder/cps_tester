import logging
import asyncio
import random
import time
import json
import sqlite3
from datetime import datetime, timedelta
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

# --- БЛОК БАЗЫ ДАННЫХ (ФУНКЦИИ) ---

def init_db():
    conn = sqlite3.connect('clicker_stats.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            user_id INTEGER,
            username TEXT,
            cps REAL,
            clicks INTEGER,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def save_user_result(user_id, username, cps, clicks):
    conn = sqlite3.connect('clicker_stats.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO results VALUES (?, ?, ?, ?, ?)', 
                   (user_id, username, cps, clicks, datetime.now()))
    conn.commit()
    conn.close()

def calculate_rank(user_id, days=None):
    conn = sqlite3.connect('clicker_stats.db')
    cursor = conn.cursor()
    query = "SELECT user_id, MAX(cps) as best_cps FROM results "
    params = []
    if days:
        date_limit = datetime.now() - timedelta(days=days)
        query += "WHERE timestamp > ? "
        params.append(date_limit)
    query += "GROUP BY user_id ORDER BY best_cps DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    for index, row in enumerate(rows):
        if row[0] == user_id:
            return index + 1
    return "???"

# --- СЛОВАРЬ ПЕРЕВОДОВ ---
LANG_DATA = {
    "ru": {
        "welcome": "Привет, {name}! 🔥\nЭто профессиональный тестер CPS :)\nПроверь свою мышку на кликабельность! (если она, конечно, выживет 🤣)\n\nЖми кнопку внизу! ⚡️🖱",
        "btn": "🎮 ТРЕНИРОВАТЬ КЛИК",
        "change": "Язык изменен на Русский 🇷🇺",
        "wait": "🤖 *AI анализирует твой позор...*",
        "ranks": ["Нубик 🐣", "Мастер 🦋", "Монстр 🐉", "КИБЕР-БОГ ⚡"],
        "headers": ["ИТОГИ ЗАМЕРА", "Скорость", "Всего кликов", "Ранг"],
        "leaderboard": "🏆 **ТВОЙ РЕЙТИНГ:**\nНеделя: #{w} | Месяц: #{m} | Всего: #{a}"
    },
    "en": {
        "welcome": "Hello, {name}! 🔥\nProfessional CPS Tester :)\nCheck your mouse durability! (if it survives, haha 🤣)\n\nPress the button below! ⚡️🖱",
        "btn": "🎮 TRAIN CLICK",
        "change": "Language changed to English 🇺🇸",
        "wait": "🤖 *AI is analyzing your performance...*",
        "ranks": ["Noob 🐣", "Pro 🦋", "Monster 🐉", "CYBER GOD ⚡"],
        "headers": ["TEST RESULTS", "Speed", "Total Clicks", "Rank"],
        "leaderboard": "🏆 **YOUR RANK:**\nWeek: #{w} | Month: #{m} | All: #{a}"
    },
    "zh": {
        "welcome": "你好, {name}! 🔥\n专业 CPS 测试器 :)\n测试你的鼠标耐用性! (如果它能活下来 🤣)\n\n点击下方按钮! ⚡️🖱",
        "btn": "🎮 开始点击训练",
        "change": "语言已更改为 中文 🇨🇳",
        "wait": "🤖 *AI 正在分析你的表现...*",
        "ranks": ["菜鸟 🐣", "高手 🦋", "怪物 🐉", "电竞之神 ⚡"],
        "headers": ["测试结果", "速度", "总点击次数", "等级"],
        "leaderboard": "🏆 **你的排名:**\n周: #{w} | 月: #{m} | 总: #{a}"
    },
    "es": {
        "welcome": "¡Hola, {name}! 🔥\nProbador de CPS profesional :)\n¡Prueba la resistencia de tu ratón! (si sobrevive 🤣)\n\n¡Pulsa el botón! ⚡️🖱",
        "btn": "🎮 ENTRENAR CLIC",
        "change": "Idioma cambiado a Español 🇪🇸",
        "wait": "🤖 *AI analizando tu rendimiento...*",
        "ranks": ["Novato 🐣", "Maestro 🦋", "Monstruo 🐉", "DIOS CIBERNÉTICO ⚡"],
        "headers": ["RESULTADOS", "Velocidad", "Clicks totales", "Rango"],
        "leaderboard": "🏆 **TU RANGO:**\nSemana: #{w} | Mes: #{m} | Total: #{a}"
    },
    "fr": {
        "welcome": "Bonjour, {name}! 🔥\nTesteur CPS professionnel :)\nTestez la survie de votre souris ! (si elle survit 🤣)\n\nAppuyez sur le bouton ! ⚡️🖱",
        "btn": "🎮 ENTRAÎNER LE CLIC",
        "change": "Langue changée en Français 🇫🇷",
        "wait": "🤖 *L'IA analyse votre performance...*",
        "ranks": ["Débutant 🐣", "Maître 🦋", "Monstre 🐉", "DIEU DU CLIC ⚡"],
        "headers": ["RÉSULTATS", "Vitesse", "Total clics", "Rang"],
        "leaderboard": "🏆 **VOTRE RANG:**\nSemaine: #{w} | Mois: #{m} | Total: #{a}"
    },
    "ar": {
        "welcome": "مرحباً {name}! 🔥\nمختبر CPS احتраفي :)\nاختبر قوة الماوس الخاص بك! (إذا نجا 🤣)\n\nاضغط على الزر! ⚡️🖱",
        "btn": "🎮 تدريب النقر",
        "change": "تم تغيير اللغة إلى العربية 🇸🇦",
        "wait": "🤖 *الذكاء الاصطناعي يحلل مستواك...*",
        "ranks": ["مبتدئ 🐣", "ماهر 🦋", "وحش 🐉", "إله النقرات ⚡"],
        "headers": ["نتائج الاختبار", "سرعة", "إجمالي النقرات", "رتبة"],
        "leaderboard": "🏆 **رتبتك:**\nأسبوع: #{w} | شهر: #{m} | الكل: #{a}"
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
    if cps < 5:
        mood = "Жестко и длинно высмей этого нуба. Он кликает как улитка. Посоветуй сменить мышку на кирпич."
    elif cps < 12:
        mood = "Саркастично подмети, что это средний результат. Не ужасно, но и гордиться нечем."
    elif cps < 20:
        mood = "Вырази уважение. Это уровень потного геймера. Спроси про смазку для свитчей."
    else:
        mood = "ПОЛНЫЙ ВОСТОРГ! Это уровень бога. Сравни его клики со скоростью света."

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "system", 
                "content": f"Ты — дерзкий геймер. {mood} Без мата. 2-3 предложения. Язык: {lang_code}."
            },
            {"role": "user", "content": f"Мой результат: {cps} CPS."}],
            max_tokens=150,
            timeout=12.0
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Неплохо, но моя микроволновка выдает больше CPS!"

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
    await callback.message.answer(L["welcome"].format(name=callback.from_user.first_name), 
                                 reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await callback.answer()

@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
    try:
        raw_data = json.loads(message.web_app_data.data)
        cps = float(raw_data.get("cps", 0))
        total = raw_data.get("total_clicks", 0)
        lang = raw_data.get("lang", "ru")
        L = LANG_DATA.get(lang, LANG_DATA["en"])
        
        # 1. СОХРАНЯЕМ В БАЗУ
        save_user_result(message.from_user.id, message.from_user.username or "Player", cps, total)
        
        # 2. СЧИТАЕМ РАНГИ
        w_rank = calculate_rank(message.from_user.id, days=7)
        m_rank = calculate_rank(message.from_user.id, days=30)
        a_rank = calculate_rank(message.from_user.id)
        
        wait = await message.answer(L["wait"], parse_mode="Markdown")
        insult = await get_ai_insult(cps, lang)
        
        r_idx = 0 if cps < 8 else 1 if cps < 15 else 2 if cps < 22 else 3
        rank_name = L["ranks"][r_idx]
        h = L["headers"]
        lb_text = L["leaderboard"].format(w=w_rank, m=m_rank, a=a_rank)

        res = (
            f"🏁 **{h[0]}**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚀 {h[1]}: **{cps} CPS**\n"
            f"🎯 {h[2]}: **{total}**\n"
            f"🏆 {h[3]}: **{rank_name}**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{lb_text}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💬 {insult}"
        )
        
        await wait.delete()
        await message.answer(res, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer("❌ Ошибка данных!")

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db() # Инициализация базы при запуске
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
