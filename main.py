# main.py
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, PreCheckoutQuery, LabeledPrice
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
import random

from config import BOT_TOKEN, THEMES, DONATION_OPTIONS
from translations import TEXTS
from premium_nicks import PREMIUM_NICKS

# === БАЗА ДАННЫХ ===
DB_NAME = "santa.db"

def init_db():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS games (
                chat_id TEXT PRIMARY KEY,
                lang TEXT DEFAULT 'ru',
                theme TEXT DEFAULT 'christmas',
                draw_time INTEGER,
                end_time INTEGER
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS players (
                user_id TEXT,
                chat_id TEXT,
                full_name TEXT,
                nick TEXT,
                gift TEXT,
                score INTEGER DEFAULT 0,
                target_id TEXT,
                premium_nick TEXT,
                PRIMARY KEY (user_id, chat_id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                player_id TEXT,
                name TEXT,
                PRIMARY KEY (player_id, name)
            )
        ''')
        db.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

# === FSM ===
class GiftState(StatesGroup):
    waiting = State()

class SetupState(StatesGroup):
    choosing_theme = State()
    waiting_draw = State()
    waiting_reveal = State()

class PremiumState(StatesGroup):
    choosing = State()

# === ГЛОБАЛЬНЫЕ ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# === ФУНКЦИИ ===
def get_lang(chat_id):
    with get_db() as db:
        row = db.execute('SELECT lang FROM games WHERE chat_id = ?', (str(chat_id),)).fetchone()
        return row['lang'] if row else 'ru'

def get_theme(chat_id):
    with get_db() as db:
        row = db.execute('SELECT theme FROM games WHERE chat_id = ?', (chat_id,)).fetchone()
        return row['theme'] if row else 'christmas'

def get_text(key, lang, **kwargs):
    return TEXTS[lang][key].format(**kwargs)

def generate_nick(theme):
    nicks = {
        'halloween': ["Призрак", "Ведьма", "Франкенштейн", "Скелетон", "Чёрная Кошка", "Мумия", "Привидение", "Зомби"],
        'office': ["Офисный Гуру", "Чайник", "Принтер", "Скрепка", "Босс", "Стажёр", "Отчёт", "Пятница"],
        'christmas': ["Санта", "Дед Мороз", "Эльф", "Снегурочка", "Гринч", "Мороз", "Снежинка", "Огонёк"]
    }
    return random.choice(nicks.get(theme, nicks['christmas'])) + str(random.randint(1, 99))

# === УСТАНОВКА КОМАНД В МЕНЮ ===
async def set_bot_commands():
    commands = [
        {"command": "start", "description": "Запустить бота"},
        {"command": "help", "description": "Помощь по игре"},
        {"command": "setup", "description": "Настроить игру"},
        {"command": "mygift", "description": "Указать желание"},
        {"command": "santabingo", "description": "Угадать личность"},
        {"command": "leaderboard", "description": "Таблица лидеров"},
        {"command": "premium", "description": "Премиум-ники"},
        {"command": "lang", "description": "Сменить язык"},
        {"command": "donate", "description": "Поддержать ⭐"}
    ]
    await bot.set_my_commands(commands)

# === ХЕНДЛЕРЫ ===
@dp.message(Command("start"))
async def start(message: Message):
    lang = get_lang(message.chat.id)
    kb = [
        [InlineKeyboardButton(text="🌟 Поддержать", pay=True)],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ]
    await message.answer(
        get_text('start', lang),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode=ParseMode.MARKDOWN
    )

@dp.callback_query(F.data == "help")
async def help(callback):
    lang = get_lang(callback.message.chat.id)
    await callback.message.edit_text(
        get_text('help', lang),
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("setup"))
async def setup(message: Message, state: FSMContext):
    lang = get_lang(message.chat.id)
    kb = []
    for theme_key, theme_name in THEMES[lang].items():
        kb.append([InlineKeyboardButton(text=theme_name, callback_data=f"theme_{theme_key}")])
    await message.reply(get_text('setup_intro', lang), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(SetupState.choosing_theme)

@dp.callback_query(F.data.startswith("theme_"))
async def set_theme(callback, state: FSMContext):
    theme = callback.data.split("_")[1]
    chat_id = str(callback.message.chat.id)
    lang = get_lang(chat_id)
    
    with get_db() as db:
        db.execute('INSERT OR REPLACE INTO games (chat_id, theme) VALUES (?, ?)', (chat_id, theme))
    
    await callback.message.answer(get_text('setup_prompt_draw', lang))
    await state.set_state(SetupState.waiting_draw)

@dp.message(SetupState.waiting_draw)
async def set_draw(message: Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        timestamp = int(dt.timestamp())
        chat_id = str(message.chat.id)
        lang = get_lang(chat_id)
        
        with get_db() as db:
            db.execute('UPDATE games SET draw_time = ? WHERE chat_id = ?', (timestamp, chat_id))
        
        scheduler.add_job(do_draw, 'date', run_date=dt, args=[chat_id])
        await message.reply(get_text('draw_set', lang, time=message.text))
        await message.reply(get_text('setup_prompt_reveal', lang))
        await state.set_state(SetupState.waiting_reveal)
    except:
        await message.reply(get_text('invalid_date', lang))

@dp.message(SetupState.waiting_reveal)
async def set_reveal(message: Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        timestamp = int(dt.timestamp())
        chat_id = str(message.chat.id)
        lang = get_lang(chat_id)
        
        with get_db() as db:
            db.execute('UPDATE games SET end_time = ? WHERE chat_id = ?', (timestamp, chat_id))
        
        scheduler.add_job(finish_game, 'date', run_date=dt, args=[chat_id])
        await message.reply(get_text('reveal_set', lang, time=message.text))
        await state.clear()
    except:
        await message.reply(get_text('invalid_date', lang))

async def do_draw(chat_id):
    with get_db() as db:
        players = db.execute('SELECT user_id FROM players WHERE chat_id = ?', (chat_id,)).fetchall()
        if len(players) < 3: return
        user_ids = [p['user_id'] for p in players]
        random.shuffle(user_ids)
        for i in range(len(user_ids)):
            giver = user_ids[i]
            receiver = user_ids[(i + 1) % len(user_ids)]
            db.execute('UPDATE players SET target_id = ? WHERE user_id = ? AND chat_id = ?', (receiver, giver, chat_id))
        
        theme = db.execute('SELECT theme FROM games WHERE chat_id = ?', (chat_id,)).fetchone()['theme']
        for i in range(len(user_ids)):
            try:
                target = db.execute('''
                    SELECT p.nick, p.gift FROM players p
                    WHERE p.user_id = ? AND p.chat_id = ?
                ''', (user_ids[(i + 1) % len(user_ids)], chat_id)).fetchone()
                msg = f"🎁 Вы дарите: {target['nick']}\n"
                if target['gift']:
                    msg += f"📝 Желание: {target['gift']}"
                await bot.send_message(user_ids[i], msg)
            except: pass
        await bot.send_message(chat_id, get_text('draw_done', get_lang(chat_id)))

async def finish_game(chat_id):
    lang = get_lang(chat_id)
    results = get_text('final_intro', lang)
    
    with get_db() as db:
        players = db.execute('''
            SELECT p.nick, p.score, p.full_name FROM players p
            WHERE p.chat_id = ?
            ORDER BY p.score DESC
        ''', (chat_id,)).fetchall()
        
        for p in players:
            achievements = db.execute('SELECT name FROM achievements WHERE player_id = ?', (p['user_id'],)).fetchall()
            ach_list = ", ".join([a['name'] for a in achievements]) if achievements else "—"
            results += f"👤 {p['nick']} | ⭐ {p['score']} | 🏆 {ach_list}\n"
        
        for p in players:
            if p['score'] >= 5:
                db.execute('INSERT OR IGNORE INTO achievements (player_id, name) VALUES (?, ?)', (p['user_id'], get_text('ach_guess_master', lang)))
            if p['score'] >= 10:
                db.execute('INSERT OR IGNORE INTO achievements (player_id, name) VALUES (?, ?)', (p['user_id'], get_text('ach_legend', lang)))
    
    await bot.send_message(chat_id, results)

@dp.message(F.new_chat_members)
async def on_join(message: Message):
    for user in message.new_chat_members:
        if user.is_bot: continue
        chat_id = str(message.chat.id)
        user_id = str(user.id)
        full_name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
        
        theme = get_theme(chat_id)
        nick = generate_nick(theme)
        
        with get_db() as db:
            db.execute('''
                INSERT OR IGNORE INTO players (user_id, chat_id, full_name, nick)
                VALUES (?, ?, ?, ?)
            ''', (user_id, chat_id, full_name, nick))
        
        lang = get_lang(chat_id)
        if db.execute('SELECT 1 FROM games WHERE chat_id = ?', (chat_id,)).fetchone():
            await message.answer(get_text('game_active', lang))

@dp.message(Command("mygift"))
async def mygift(message: Message, state: FSMContext):
    lang = get_lang(message.chat.id)
    await message.reply(get_text('gift_prompt', lang))
    await state.set_state(GiftState.waiting)

@dp.message(GiftState.waiting)
async def set_gift(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    
    with get_db() as db:
        db.execute('UPDATE players SET gift = ? WHERE user_id = ? AND chat_id = ?', (message.text, user_id, chat_id))
    
    await message.reply(get_text('gift_saved', lang))
    await state.clear()

@dp.message(Command("santabingo"))
async def santabingo(message: Message):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    
    with get_db() as db:
        players = db.execute('SELECT nick, user_id FROM players WHERE chat_id = ?', (chat_id,)).fetchall()
        targets = [p for p in players if p['user_id'] != str(message.from_user.id)]
        if not targets: return
        
        target = random.choice(targets)
        kb = []
        shuffled = random.sample(players, len(players))
        for p in shuffled:
            kb.append([InlineKeyboardButton(text=p['nick'], callback_data=f"guess_{target['user_id']}_{p['user_id']}")])
        
        await message.reply(get_text('santabingo_intro', lang, nick=target['nick']), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("guess_"))
async def process_guess(callback):
    _, target_id, selected_id = callback.data.split("_")
    user_id = str(callback.from_user.id)
    chat_id = str(callback.message.chat.id)
    lang = get_lang(chat_id)
    
    correct = target_id == selected_id
    with get_db() as db:
        if correct:
            db.execute('UPDATE players SET score = score + 1 WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
            await callback.message.edit_text(get_text('guess_correct', lang))
        else:
            name = db.execute('SELECT full_name FROM players WHERE user_id = ? AND chat_id = ?', (target_id, chat_id)).fetchone()
            await callback.message.edit_text(get_text('guess_wrong', lang, name=name['full_name'] if name else "Unknown"))
    await callback.answer()

@dp.message(Command("leaderboard"))
async def leaderboard(message: Message):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    
    with get_db() as db:
        players = db.execute('''
            SELECT nick, score FROM players
            WHERE chat_id = ?
            ORDER BY score DESC
            LIMIT 10
        ''', (chat_id,)).fetchall()
        
        text = get_text('leaderboard', lang)
        for i, p in enumerate(players, 1):
            text += f"{i}. {p['nick']} — {p['score']} очков\n"
    
    await message.reply(text)

@dp.message(Command("premium"))
async def premium(message: Message, state: FSMContext):
    chat_id = str(message.chat.id)
    lang = get_lang(chat_id)
    theme = get_theme(chat_id)
    
    if theme not in PREMIUM_NICKS[lang]:
        await message.reply("❌ Тема не установлена.")
        return
    
    nicks = PREMIUM_NICKS[lang][theme]
    kb = [[InlineKeyboardButton(text=f"✨ {n}", callback_data=f"buy_{n}")] for n in nicks]
    await message.reply(get_text('premium_intro', lang), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(PremiumState.choosing)

@dp.callback_query(F.data.startswith("buy_"))
async def buy_nick(callback, state: FSMContext):
    nick = callback.data.replace("buy_", "")
    chat_id = str(callback.message.chat.id)
    lang = get_lang(chat_id)
    
    with get_db() as db:
        if db.execute('SELECT 1 FROM players WHERE premium_nick = ? AND chat_id = ?', (nick, chat_id)).fetchone():
            await callback.message.edit_text(get_text('premium_sold', lang))
            return
    
    prices = [LabeledPrice(label="Премиум-ник", amount=50)]
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title="Разблокировать ник",
        description=f"Ник: {nick}",
        provider_token="",
        currency="XTR",
        prices=prices,
        payload=f"premium_{nick}_{chat_id}",
        need_name=False
    )
    await state.update_data(pending_nick=nick, chat_id=chat_id)

@dp.pre_checkout_query()
async def checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def success_pay(message: Message):
    data = message.successful_payment.invoice_payload
    parts = data.split("_")
    if len(parts) < 3:
        return
    nick = "_".join(parts[1:-1])
    chat_id = parts[-1]
    user_id = str(message.from_user.id)
    
    with get_db() as db:
        player = db.execute('SELECT chat_id FROM players WHERE user_id = ?', (user_id,)).fetchone()
        if not player or player['chat_id'] != chat_id:
            await message.answer("❌ Вы не участвуете в этой игре.")
            return
        
        # Проверим, не куплен ли ник
        if db.execute('SELECT 1 FROM players WHERE premium_nick = ? AND chat_id = ?', (nick, chat_id)).fetchone():
            await message.answer("🚫 Этот ник уже куплен.")
            return
        
        db.execute('UPDATE players SET nick = ?, premium_nick = ? WHERE user_id = ? AND chat_id = ?', 
                  (nick, nick, user_id, chat_id))
    
    lang = get_lang(chat_id)
    await message.answer(get_text('nick_unlocked', lang, nick=nick))

@dp.message(Command("lang"))
async def change_lang(message: Message):
    chat_id = str(message.chat.id)
    with get_db() as db:
        db.execute('UPDATE games SET lang = ? WHERE chat_id = ?', ('en' if get_lang(chat_id) == 'ru' else 'ru', chat_id))
    lang = get_lang(chat_id)
    await message.reply(get_text('lang_changed', lang))

@dp.message(Command("donate"))
async def donate(message: Message):
    lang = get_lang(message.chat.id)
    prices = [LabeledPrice(label=f"{amt} звёзд", amount=amt) for amt in DONATION_OPTIONS]
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Поддержать бота",
        description="Спасибо за поддержку!",
        provider_token="",
        currency="XTR",
        prices=prices,
        payload="donation",
        need_name=False
    )

# === ЗАПУСК ===
async def main():
    init_db()
    await set_bot_commands()
    scheduler.start()
    print("✅ Secret Santa Bot запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())