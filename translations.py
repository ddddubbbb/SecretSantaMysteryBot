# translations.py
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
        'premium_locked': "🔒 Этот ник уже занят или недоступен.",
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
        'premium_locked': "🔒 This nick is already taken or unavailable.",
        'premium_sold': "🚫 This nick is already purchased by another player."
    }
}