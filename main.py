# main.py
import asyncio
import logging
import traceback
from typing import Optional, List, Dict, Any
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, InlineKeyboardButton, InlineKeyboardMarkup, 
    PreCheckoutQuery, LabeledPrice, ChatMemberOwner, ChatMemberAdministrator
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode, ChatType
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
import random
import hashlib

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не установлен")

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === ПЕРЕВОДЫ ===
TEXTS = {
    'ru': {
        'start': "🎁 Привет! Я — бот для *Тайного Санты*.\n\n"
                 "Добавьте меня в группу, и я помогу организовать игру с подарками, угадываниями и анонимностью.",
        'help': "📖 *Как играть*\n\n"
                "1. Добавьте бота в группу\n"
                "2. Назначьте его админом\n"
                "3. Используйте /setup, чтобы выбрать тему и даты\n"
                "4. Все участники автоматически зарегистрированы\n"
                "5. Каждый пишет, что хочет в подарок (/mygift)\n"
                "6. В день жеребьёвки — вы узнаете, кому дарите\n"
                "7. Угадывайте, кто за каким ником — получайте очки!\n"
                "8. В день раскрытия — финал: таблица, ачивки, смех\n\n"
                "🔹 /setup — настроить игру\n"
                "🔹 /mygift — указать желание\n"
                "🔹 /santabingo — угадать личность\n"
                "🔹 /leaderboard — таблица лидеров\n"
                "🔹 /lang — сменить язык\n"
                "🔹 /premium — премиум-ники\n"
                "🔹 /donate — поддержать ⭐",
        'donate': "🙏 Спасибо за поддержку!\n\n"
                  "Вы можете отправить звёзды Telegram, чтобы помочь в развитии бота.",
        'setup_intro': "🎨 Выберите тему игры:",
        'setup_prompt_draw': "📅 Установите дату жеребьёвки (ДД.ММ.ГГГГ ЧЧ:ММ):",
        'setup_prompt_reveal': "📅 Установите дату раскрытия (когда покажем, кто за каким ником):",
        'draw_set': "🎉 Жеребьёвка назначена на {time}",
        'reveal_set': "🎉 Дата раскрытия установлена на {time}",
        'invalid_date': "❌ Неверный формат. Пример: 25.12.2025 18:00",
        'game_active': "✅ Все участники зарегистрированы.",
        'gift_prompt': "🎁 Напишите, что вы хотите получить:",
        'gift_saved': "✅ Ваше желание сохранено!",
        'draw_done': "🎉 Жеребьёвка завершена! Все получили своих 'подопечных'.",
        'final_intro': "🎊 Игра завершена! Все личности раскрыты:\n\n",
        'ach_guess_master': "Мастер Угадывания",
        'ach_legend': "Легенда вечеринки",
        'leaderboard': "🏆 Таблица лидеров:\n\n{list}",
        'santabingo_intro': "🔍 Кто скрывается за ником *{nick}*?\nВыберите реальное имя:",
        'guess_correct': "✅ Правильно! +1 очко",
        'guess_wrong': "❌ Неверно. Это был {name}",
        'lang_changed': "✅ Язык изменён на русский",
        'theme_selected': "🎨 Тема установлена: {theme}",
        'premium_intro': "✨ Разблокируйте премиум-ник за 50 звёзд Telegram!\nВыберите один:",
        'nick_unlocked': "🎉 Ник активирован: {nick}\n\n✨ Спасибо за поддержку! Ты сделал праздник ярче!",
        'premium_sold': "🚫 Этот ник уже куплен другим участником."
    },
    'en': {
        'start': "🎁 Hi! I'm a *Secret Santa* bot.\n\n"
                 "Add me to a group and I'll help organize gifts, guessing, and anonymity.",
        'help': "📖 *How to play*\n\n"
                "1. Add bot to group\n"
                "2. Make it admin\n"
                "3. Use /setup to choose theme and dates\n"
                "4. All members auto-registered\n"
                "5. Each writes their gift wish (/mygift)\n"
                "6. On draw day — you'll know who to gift\n"
                "7. Guess who's behind nicks — earn points!\n"
                "8. On reveal day — final: leaderboard, achievements, fun\n\n"
                "🔹 /setup — configure game\n"
                "🔹 /mygift — set wish\n"
                "🔹 /santabingo — guess identity\n"
                "🔹 /leaderboard — leaderboard\n"
                "🔹 /lang — change language\n"
                "🔹 /premium — premium nicks\n"
                "🔹 /donate — support ⭐",
        'donate': "🙏 Thank you for your support!\n\n"
                  "You can send Telegram Stars to help develop the bot.",
        'setup_intro': "🎨 Choose game theme:",
        'setup_prompt_draw': "📅 Set draw date (DD.MM.YYYY HH:MM):",
        'setup_prompt_reveal': "📅 Set reveal date (when we show who was behind nicks):",
        'draw_set': "🎉 Draw set to {time}",
        'reveal_set': "🎉 Reveal date set to {time}",
        'invalid_date': "❌ Invalid format. Example: 12.31.2025 20:00",
        'game_active': "✅ All members registered.",
        'gift_prompt': "🎁 Write what you'd like to receive:",
        'gift_saved': "✅ Your wish saved!",
        'draw_done': "🎉 Draw completed! Everyone got their target.",
        'final_intro': "🎊 Game finished! All identities revealed:\n\n",
        'ach_guess_master': "Guessing Master",
        'ach_legend': "Party Legend",
        'leaderboard': "🏆 Leaderboard:\n\n{list}",
        'santabingo_intro': "🔍 Who is behind *{nick}*?\nChoose real name:",
        'guess_correct': "✅ Correct! +1 point",
        'guess_wrong': "❌ Wrong. It was {name}",
        'lang_changed': "✅ Language changed to English",
        'theme_selected': "🎨 Theme set: {theme}",
        'premium_intro': "✨ Unlock a premium nick for 50 Telegram Stars!\nChoose one:",
        'nick_unlocked': "🎉 Nick unlocked: {nick}\n\n✨ Thank you for support! You made the party brighter!",
        'premium_sold': "🚫 This nick is already purchased by another player."
    }
}

# === ПРЕМИУМ-НИКИ ПО ТЕМАМ ===
PREMIUM_NICKS = {
    'ru': {
        'christmas': ["Санта", "Гринч", "Скрудж", "Снегурочка", "Баба Яга", "Снежная Королева", "Дед Мороз", "Олаф", "Эльза", "Анна"],
        'halloween': ["Ведьма", "Призрак", "Вампир", "Оборотень", "Франкенштейн", "Зомби", "Мумия", "Пум-Бум", "Чёрная Кошка", "Джек-фонарь"],
        'office': ["Дуайт", "Джим", "Майкл", "Принтер", "Скрепка", "Кофе", "Стол", "Стул", "Лампа", "Папка"]
    },
    'en': {
        'christmas': ["Santa", "Grinch", "Scrooge", "Snegurochka", "Baba Yaga", "Snow Queen", "Father Frost", "Olaf", "Elsa", "Anna"],
        'halloween': ["Witch", "Ghost", "Vampire", "Werewolf", "Frankenstein", "Zombie", "Mummy", "Pumpking", "Black Cat", "JackOlantern"],
        'office': ["Dwight", "Jim", "Michael", "Printer", "Stapler", "Coffee", "Desk", "Chair", "Lamp", "Folder"]
    }
}

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
def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Очищает пользовательский ввод от потенциально опасных символов"""
    if not text:
        return ""
    
    # Убираем потенциально опасные символы
    import re
    sanitized = re.sub(r'[<>"\';]', '', str(text)[:max_length])
    return sanitized.strip()

def get_lang(chat_id):
    try:
        with get_db() as db:
            row = db.execute('SELECT lang FROM games WHERE chat_id = ?', (str(chat_id),)).fetchone()
            return row['lang'] if row else 'ru'
    except Exception as e:
        logger.error(f"Ошибка получения языка: {e}")
        return 'ru'

def get_theme(chat_id):
    with get_db() as db:
        row = db.execute('SELECT theme FROM games WHERE chat_id = ?', (chat_id,)).fetchone()
        return row['theme'] if row else 'christmas'

def get_text(key, lang, **kwargs):
    return TEXTS[lang][key].format(**kwargs)

def generate_nick(theme):
    """Генерирует случайный ник на основе темы"""
    base_nicks = {
        'christmas': ["Санта", "Эльф", "Мороз", "Подарок", "Новогодик", "Снежок", "Олень", "Елочка"],
        'halloween': ["Призрак", "Ведьма", "Тыква", "Летучая Мышь", "Паук", "Скелет", "Вампир", "Оборотень"],
        'office': ["Кофе", "Принтер", "Папка", "Степлер", "Монитор", "Стол", "Стул", "Лампа"]
    }
    
    prefixes = base_nicks.get(theme, base_nicks['christmas'])
    suffixes = [str(i).zfill(2) for i in range(1, 99)]
    return random.choice(prefixes) + random.choice(suffixes)

async def is_admin(chat_id: int, user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором чата"""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))
    except Exception as e:
        logger.error(f"Ошибка проверки прав администратора: {e}")
        return False

async def register_all_members(chat_id: str, theme: str = 'christmas'):
    """Регистрирует всех участников группы в игре"""
    try:
        # Получаем список всех участников чата
        chat_members = []
        async for member in bot.iter_chat_members(int(chat_id)):
            if not member.user.is_bot and member.status != 'left':
                chat_members.append(member.user)
        
        logger.info(f"Найдено {len(chat_members)} участников в чате {chat_id}")
        
        with get_db() as db:
            for user in chat_members:
                user_id = str(user.id)
                full_name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
                nick = generate_nick(theme)
                
                # Проверяем, что ник уникальный
                while db.execute('SELECT 1 FROM players WHERE nick = ? AND chat_id = ?', (nick, chat_id)).fetchone():
                    nick = generate_nick(theme)
                
                db.execute('''
                    INSERT OR REPLACE INTO players (user_id, chat_id, full_name, nick)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, chat_id, full_name, nick))
        
        return len(chat_members)
    except Exception as e:
        logger.error(f"Ошибка регистрации участников: {e}")
        return 0

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
    # Проверяем, что команда вызвана в группе
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Эта команда работает только в группах.")
        return
    
    # Проверяем админские права
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("❌ Только администраторы могут настраивать игру.")
        return
    
    lang = get_lang(message.chat.id)
    kb = [
        [InlineKeyboardButton(text="🎄 Рождество", callback_data="theme_christmas")],
        [InlineKeyboardButton(text="🎃 Хэллоуин", callback_data="theme_halloween")],
        [InlineKeyboardButton(text="👔 Корпоратив", callback_data="theme_office")]
    ]
    await message.reply(get_text('setup_intro', lang), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(SetupState.choosing_theme)

@dp.callback_query(F.data.startswith("theme_"))
async def set_theme(callback, state: FSMContext):
    theme = callback.data.split("_")[1]
    chat_id = str(callback.message.chat.id)
    lang = get_lang(chat_id)
    
    with get_db() as db:
        db.execute('INSERT OR REPLACE INTO games (chat_id, theme) VALUES (?, ?)', (chat_id, theme))
    
    # Автоматически регистрируем всех участников группы
    registered_count = await register_all_members(chat_id, theme)
    
    await callback.message.answer(
        f"✅ Тема установлена: {theme}\n"
        f"👥 Зарегистрировано участников: {registered_count}\n\n"
        f"{get_text('setup_prompt_draw', lang)}"
    )
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
    """Проводит жеребьевку и назначает участников"""
    try:
        with get_db() as db:
            players = db.execute('SELECT user_id FROM players WHERE chat_id = ?', (chat_id,)).fetchall()
            if len(players) < 2:  # Минимум 2 участника
                await bot.send_message(chat_id, "❌ Недостаточно участников для жеребьевки (минимум 2)")
                return
            
            user_ids = [p['user_id'] for p in players]
            random.shuffle(user_ids)
            
            # Назначаем получателей подарков
            for i in range(len(user_ids)):
                giver = user_ids[i]
                receiver = user_ids[(i + 1) % len(user_ids)]
                db.execute('UPDATE players SET target_id = ? WHERE user_id = ? AND chat_id = ?', (receiver, giver, chat_id))
            
            # Отправляем уведомления участникам
            for i in range(len(user_ids)):
                try:
                    target = db.execute('''
                        SELECT p.nick, p.gift FROM players p
                        WHERE p.user_id = ? AND p.chat_id = ?
                    ''', (user_ids[(i + 1) % len(user_ids)], chat_id)).fetchone()
                    
                    msg = f"🎁 Ваш получатель подарка: {target['nick']}\n"
                    if target['gift']:
                        msg += f"📝 Их желание: {target['gift']}"
                    else:
                        msg += "📝 Желание пока не указано"
                    
                    await bot.send_message(user_ids[i], msg)
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения пользователю {user_ids[i]}: {e}")
            
            lang = get_lang(chat_id)
            await bot.send_message(chat_id, get_text('draw_done', lang))
            logger.info(f"Жеребьевка завершена для чата {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка проведения жеребьевки: {e}")
        await bot.send_message(chat_id, "❌ Произошла ошибка во время жеребьевки")

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
    """Обрабатывает добавление новых участников в группу"""
    try:
        for user in message.new_chat_members:
            if user.is_bot: 
                continue
            
            chat_id = str(message.chat.id)
            user_id = str(user.id)
            full_name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
            
            # Проверяем, есть ли активная игра
            with get_db() as db:
                game = db.execute('SELECT theme FROM games WHERE chat_id = ?', (chat_id,)).fetchone()
                if not game:
                    continue  # Нет активной игры
                
                theme = game['theme']
                nick = generate_nick(theme)
                
                # Убеждаемся, что ник уникален
                while db.execute('SELECT 1 FROM players WHERE nick = ? AND chat_id = ?', (nick, chat_id)).fetchone():
                    nick = generate_nick(theme)
                
                db.execute('''
                    INSERT OR IGNORE INTO players (user_id, chat_id, full_name, nick)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, chat_id, full_name, nick))
            
            lang = get_lang(chat_id)
            await message.answer(f"👋 {full_name} присоединился к игре с ником {nick}!")
            logger.info(f"Новый участник {full_name} добавлен в игру {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка обработки новых участников: {e}")

@dp.message(Command("mygift"))
async def mygift(message: Message, state: FSMContext):
    lang = get_lang(message.chat.id)
    await message.reply(get_text('gift_prompt', lang))
    await state.set_state(GiftState.waiting)

@dp.message(GiftState.waiting)
async def set_gift(message: Message, state: FSMContext):
    """Сохраняет желание пользователя с валидацией"""
    try:
        user_id = str(message.from_user.id)
        chat_id = str(message.chat.id)
        lang = get_lang(chat_id)
        
        # Валидация ввода
        gift_text = sanitize_input(message.text, max_length=500)
        if not gift_text or len(gift_text.strip()) < 3:
            await message.reply("❌ Желание должно содержать минимум 3 символа.")
            return
        
        with get_db() as db:
            db.execute('UPDATE players SET gift = ? WHERE user_id = ? AND chat_id = ?', (gift_text, user_id, chat_id))
        
        await message.reply(get_text('gift_saved', lang))
        await state.clear()
        logger.info(f"Пользователь {user_id} установил желание в чате {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка сохранения желания: {e}")
        await message.reply("❌ Произошла ошибка при сохранении желания.")

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
        
        if db.execute('SELECT 1 FROM players WHERE premium_nick = ? AND chat_id = ?', (nick, chat_id)).fetchone():
            await message.answer("🚫 Этот ник уже куплен.")
            return
        
        db.execute('UPDATE players SET nick = ?, premium_nick = ? WHERE user_id = ? AND chat_id = ?', 
                  (nick, nick, user_id, chat_id))
    
    lang = get_lang(chat_id)
    await message.answer(get_text('nick_unlocked', lang, nick=nick))

@dp.message(Command("info"))
async def game_info(message: Message):
    """Показывает информацию о текущей игре"""
    chat_id = str(message.chat.id)
    
    with get_db() as db:
        game = db.execute('SELECT * FROM games WHERE chat_id = ?', (chat_id,)).fetchone()
        if not game:
            await message.reply("❌ Игра не настроена. Используйте /setup для начала.")
            return
        
        players_count = db.execute('SELECT COUNT(*) as cnt FROM players WHERE chat_id = ?', (chat_id,)).fetchone()['cnt']
        
        info_text = f"🎮 **Информация об игре**\n\n"
        info_text += f"🎨 Тема: {game['theme']}\n"
        info_text += f"👥 Участников: {players_count}\n"
        
        if game['draw_time']:
            draw_dt = datetime.fromtimestamp(game['draw_time'])
            info_text += f"🎲 Жеребьевка: {draw_dt.strftime('%d.%m.%Y %H:%M')}\n"
        
        if game['end_time']:
            end_dt = datetime.fromtimestamp(game['end_time'])
            info_text += f"🎊 Раскрытие: {end_dt.strftime('%d.%m.%Y %H:%M')}\n"
        
        info_text += f"🌍 Язык: {game['lang']}"
    
    await message.reply(info_text, parse_mode=ParseMode.MARKDOWN)

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
    prices = [LabeledPrice(label=f"{amt} звёзд", amount=amt) for amt in [1, 10, 25, 50, 100, 500, 1000, 5000]]
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

# === ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ОШИБОК ===
@dp.error()
async def error_handler(update, exception):
    """Глобальный обработчик ошибок"""
    logger.error(f"Ошибка обработки обновления {update}: {exception}")
    logger.error(traceback.format_exc())
    
    # Попытка отправить уведомление пользователю
    try:
        if hasattr(update, 'message') and update.message:
            await update.message.reply("❌ Произошла ошибка. Попробуйте позже.")
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply("❌ Произошла ошибка. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

# === ЗАПУСК ===
async def main():
    try:
        init_db()
        await set_bot_commands()
        scheduler.start()
        logger.info("✅ Secret Santa Bot запущен и готов к работе!")
        print("✅ Secret Santa Bot запущен и готов к работе!")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Критическая ошибка запуска: {e}")
        raise
    finally:
        scheduler.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise