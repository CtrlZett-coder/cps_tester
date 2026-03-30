import logging
import asyncio
import time
import json
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from openai import AsyncOpenAI

# --- НАСТРОЙКИ ---
TOKEN = "8733664979:AAH8lQgeDFfsQcXENuPgh5AG4UzrXBYz7gU"
BASE_URL = "https://ctrlzett-coder.github.io/cps_tester/"
DEEPSEEK_KEY = "sk-b0241be117b0481e99ecb1446330f8f6"

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = AsyncOpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

# --- СИСТЕМА РАНГОВ ---
def get_rank(cps, lang):
    ranks = {
        "ru": [(0, "Улитка 🐌"), (5, "Новичок 👨‍💻"), (10, "Профи 🔥"), (15, "Читер? ⚡️"), (20, "БОГ КЛИКОВ 👑")],
        "en": [(0, "Snail 🐌"), (5, "Rookie 👨‍💻"), (10, "Pro 🔥"), (15, "Cheater? ⚡️"), (20, "CLICK GOD 👑")],
        "zh": [(0, "蜗牛 🐌"), (5, "新手 👨‍💻"), (10, "高手 🔥"), (15, "外挂？ ⚡️"), (20, "点击之神 👑")],
        "es": [(0, "Caracol 🐌"), (5, "Novato 👨‍💻"), (10, "Pro 🔥"), (15, "¿Hacker? ⚡️"), (20, "DIOS DEL CLICK 👑")],
        "fr": [(0, "Escargot 🐌"), (5, "Recrue 👨‍💻"), (10, "Pro 🔥"), (15, "Cheat? ⚡️"), (20, "DIEU DU CLIC 👑")],
        "ar": [(0, "حلزون 🐌"), (5, "مبتدئ 👨‍💻"), (10, "محترف 🔥"), (15, "غشاش؟ ⚡️"), (20, "إله النقر 👑")]
    }
    current_ranks = ranks.get(lang, ranks["en"])
    user_rank = current_ranks[0][1]
    for threshold, label in current_ranks:
        if cps >= threshold:
            user_rank = label
    return user_rank

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('clicker_stats.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS results 
                      (user_id INTEGER, username TEXT, cps REAL, clicks INTEGER, timestamp DATETIME)''')
    conn.commit()
    conn.close()

def save_user_result(user_id, username, cps, clicks):
    conn = sqlite3.connect('clicker_stats.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO results VALUES (?, ?, ?, ?, ?)', 
                   (user_id, username, cps, clicks, datetime.now()))
    conn.commit()
    conn.close()

def get_top_list(user_id, lang, period_days=None):
    conn = sqlite3.connect('clicker_stats.db')
    cursor = conn.cursor()
    query = "SELECT user_id, username, MAX(cps), MAX(clicks) FROM results "
    params = []
    if period_days:
        date_limit = datetime.now() - timedelta(days=period_days)
        query += "WHERE timestamp > ? "
        params.append(date_limit)
    query += "GROUP BY user_id ORDER BY MAX(cps) DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    L = LANG_DATA.get(lang, LANG_DATA["en"])
    # Исправленный выбор заголовка топа
    if period_days == 7: title = L["top_titles"][0]
    elif period_days == 30: title = L["top_titles"][1]
    else: title = L["top_titles"][2]

    text = f"🏆 **{title}**\n━━━━━━━━━━━━━━━\n"
    user_line = ""
    for i, row in enumerate(rows):
        uid, name, cps, clks = row
        rank_idx = i + 1
        name = name if name and name != "None" else "Player"
        medal = "🥇" if rank_idx == 1 else "🥈" if rank_idx == 2 else "🥉" if rank_idx == 3 else f"{rank_idx}."
        if rank_idx <= 5: text += f"{medal} {name} — **{cps}** CPS\n"
        if uid == user_id: user_line = f"━━━━━━━━━━━━━━━\n{L['your_place']}: {rank_idx}. {name} — {cps} CPS"
    
    if not rows: text += "Пока нет результатов..."
    return text + user_line

# --- СЛОВАРЬ (ПОЛНЫЙ) ---
LANG_DATA = {
    "ru": {
        "welcome": "Привет, {name}! 🔥🔥🔥\nЭто **профессиональный** КПС трекер!\nПроверь свою мышку на **СКОРОСТЬ** и **КЛИКИ**! (если она, конечно, выживет 🤣)\nНачинай кликать **ПРЯМО СЕЙЧАС**!\nЖми кнопку снизу",
        "btn": "🎮 ТРЕНИРОВАТЬ КЛИК", "change": "Язык изменен на Русский 🇷🇺", "wait": "🤖 *AI анализирует результат...*",
        "headers": ["ИТОГИ ЗАМЕРА", "Скорость", "Всего", "Ранг"], "top_btn": "📊 Топ Ранг",
        "top_titles": ["ТОП НЕДЕЛИ", "ТОП МЕСЯЦА", "ТОП ВСЕ ВРЕМЯ"], "your_place": "Ваше место", "nav": ["Неделя", "Месяц", "Всего", "« Назад"]
    },
    "en": {
        "welcome": "Hello, {name}! 🔥🔥🔥\nThis is a **professional** CPS tracker!\nCheck your mouse for **SPEED** and **CLICKS**! (if it survives, of course 🤣)\nStart clicking **RIGHT NOW**!\nPress the button below",
        "btn": "🎮 TRAIN CLICK", "change": "Language changed to English 🇺🇸", "wait": "🤖 *AI is analyzing...*",
        "headers": ["TEST RESULTS", "Speed", "Total", "Rank"], "top_btn": "📊 Top Rank",
        "top_titles": ["WEEKLY TOP", "MONTHLY TOP", "ALL TIME TOP"], "your_place": "Your place", "nav": ["Week", "Month", "All", "« Back"]
    },
    "zh": {
        "welcome": "你好, {name}! 🔥🔥🔥\n这是一个**专业**的 CPS 测试器！\n**现在**就开始点击！",
        "btn": "🎮 开始训练", "change": "语言已更改 🇨🇳", "wait": "🤖 *分析中...*",
        "headers": ["测试结果", "速度", "总计", "等级"], "top_btn": "📊 排名",
        "top_titles": ["周榜", "月榜", "总榜"], "your_place": "你的位置", "nav": ["周", "月", "总", "« 返回"]
    },
    "es": {
        "welcome": "¡Hola, {name}! 🔥🔥🔥\n¡Rastreador de CPS **profesional**!\n¡Empieza a hacer clic **AHORA MISMO**!",
        "btn": "🎮 ENTRENAR", "change": "Idioma cambiado 🇪🇸", "wait": "🤖 *IA analizando...*",
        "headers": ["RESULTADOS", "Velocidad", "Total", "Rango"], "top_btn": "📊 Ranking",
        "top_titles": ["TOP SEMANA", "TOP MES", "TOP TOTAL"], "your_place": "Tu lugar", "nav": ["Semana", "Mes", "Todo", "« Volver"]
    },
    "fr": {
        "welcome": "Bonjour, {name}! 🔥🔥🔥\nTracker CPS **professionnel** !",
        "btn": "🎮 ENTRAÎNER", "change": "Langue changée 🇫🇷", "wait": "🤖 *Analyse...*",
        "headers": ["RÉSULTATS", "Vitesse", "Total", "Rang"], "top_btn": "📊 Classement",
        "top_titles": ["TOP SEMAINE", "TOP MOIS", "TOP TOTAL"], "your_place": "Votre place", "nav": ["Semaine", "Mois", "Tout", "« Retour"]
    },
    "ar": {
        "welcome": "مرحباً {name}! 🔥🔥🔥\nهذا متتبع CPS **احترافي**!",
        "btn": "🎮 تدريب", "change": "تم تغيير اللغة 🇸🇦", "wait": "🤖 *تحليل...*",
        "headers": ["النتائج", "سرعة", "إجمالي", "رتبة"], "top_btn": "📊 الترتيب",
        "top_titles": ["أفضل الأسبوع", "أفضل الشهر", "الكل"], "your_place": "مكانك", "nav": ["أسبوع", "شهر", "الكل", "« عودة"]
    }
}

# --- КЛАВИАТУРЫ ---
def get_top_kb(lang):
    L = LANG_DATA.get(lang, LANG_DATA["en"])
    builder = InlineKeyboardBuilder()
    builder.button(text=L["nav"][0], callback_data=f"top_7_{lang}")
    builder.button(text=L["nav"][1], callback_data=f"top_30_{lang}")
    builder.button(text=L["nav"][2], callback_data=f"top_all_{lang}")
    builder.button(text=L["nav"][3], callback_data=f"top_back_{lang}")
    builder.adjust(3, 1)
    return builder.as_markup()

# --- AI ФУНКЦИЯ ---
async def get_ai_insult(cps, lang_code):
    system_prompt = (
        f"You are a professional gaming commentator. Rate the user's {cps} CPS. "
        "If CPS > 15, be impressed but sarcastic (like 'Are you even human?'). "
        "If CPS < 7, roast them for being a snail. Use humor. "
        f"Response must be in {lang_code} language. Max 20 words. Be expressive."
    )
    try:
        res = await client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": system_prompt}], timeout=10.0)
        return res.choices[0].message.content
    except: return "🔥"

# --- ОБРАБОТЧИКИ ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    flags = {"ru": "🇷🇺", "en": "🇺🇸", "zh": "🇨🇳", "es": "🇪🇸", "fr": "🇫🇷", "ar": "🇸🇦"}
    for code, flag in flags.items():
        builder.button(text=f"{code.upper()} {flag}", callback_data=f"lang_{code}")
    builder.adjust(2)
    await message.answer("🌐 Choose language / Выберите язык:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    L = LANG_DATA.get(lang, LANG_DATA["en"])
    url = f"{BASE_URL}?v={int(time.time())}&lang={lang}"
    webapp_kb = [[types.KeyboardButton(text=L["btn"], web_app=types.WebAppInfo(url=url))]]
    inline_kb = InlineKeyboardBuilder()
    inline_kb.button(text=L["top_btn"], callback_data=f"top_7_{lang}")
    await callback.message.answer(L["change"])
    await callback.message.answer(L["welcome"].format(name=callback.from_user.first_name), reply_markup=inline_kb.as_markup(), parse_mode="Markdown")
    await callback.message.answer("⏬", reply_markup=types.ReplyKeyboardMarkup(keyboard=webapp_kb, resize_keyboard=True))
    await callback.answer()

@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        cps = float(data.get("cps", 0))
        total = data.get("total_clicks", 0)
        lang = data.get("lang", "en")
        
        save_user_result(message.from_user.id, message.from_user.username or message.from_user.first_name, cps, total)
        L = LANG_DATA.get(lang, LANG_DATA["en"])
        rank_label = get_rank(cps, lang)
        
        wait = await message.answer(L["wait"], parse_mode="Markdown")
        insult = await get_ai_insult(cps, lang)
        
        kb = InlineKeyboardBuilder()
        kb.button(text=L["top_btn"], callback_data=f"top_7_{lang}")
        
        h = L["headers"]
        res = (f"🏁 **{h[0]}**\n━━━━━━━━━━━━━━━\n"
               f"🚀 {h[1]}: **{cps} CPS**\n🎯 {h[2]}: **{total}**\n🏆 {h[3]}: **{rank_label}**\n"
               f"━━━━━━━━━━━━━━━\n💬 {insult}")
        
        await wait.delete()
        await message.answer(res, reply_markup=kb.as_markup(), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error: {e}")

@dp.callback_query(F.data.startswith("top_"))
async def handle_top(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    action = parts[1]
    lang = parts[2]
    
    if action == "back":
        L = LANG_DATA.get(lang, LANG_DATA["en"])
        inline_kb = InlineKeyboardBuilder()
        inline_kb.button(text=L["top_btn"], callback_data=f"top_7_{lang}")
        await callback.message.delete()
        await callback.message.answer(L["welcome"].format(name=callback.from_user.first_name), reply_markup=inline_kb.as_markup(), parse_mode="Markdown")
        return

    days = 7 if action == "7" else 30 if action == "30" else None
    text = get_top_list(callback.from_user.id, lang, days)
    await callback.message.edit_text(text, reply_markup=get_top_kb(lang), parse_mode="Markdown")
    await callback.answer()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
