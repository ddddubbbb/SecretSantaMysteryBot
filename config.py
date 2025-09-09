# config.py
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

# Темы с иконками
THEMES = {
    'ru': {
        'christmas': '🎄 Рождество',
        'halloween': '🎃 Хэллоуин',
        'office': '👔 Корпоратив'
    },
    'en': {
        'christmas': '🎄 Christmas',
        'halloween': '🎃 Halloween',
        'office': '👔 Office Party'
    }
}

# Звёзды
DONATION_OPTIONS = [1, 10, 25, 50, 100, 500, 1000, 5000]