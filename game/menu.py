from telebot import types as tele_types

# 1. ГЛАВНОЕ МЕНЮ ИГР (Центральный хаб)
def get_main_games_menu():
    report = (
        "🌌 **ИГРОВОЙ ОТСЕК АКАДЕМИИ ОРИОН** 🌌\n"
        "──────────────────────────\n"
        "Выберите активную симуляцию из списка ниже. Каждое решение влияет на ваш ранг и запас Звездной Пыли.\n\n"
        "📡 **ДОСТУПНЫЕ МИССИИ:**"
    )
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        # Кнопка старой игры
        tele_types.InlineKeyboardButton("🚀 Дневник юного космонавта", callback_data="game_select_diary"),
        
        # Кнопка НОВОЙ игры
        tele_types.InlineKeyboardButton("☢️ Протокол: Чистое Небо (NEW)", callback_data="apoc_start"),
        
        tele_types.InlineKeyboardButton("🏆 Рейтинг пилотов", callback_data="game_instruction_fix")
    )
    return report, kb

# 2. МЕНЮ ГЛАВ (Описание и дорожная карта)
def get_diary_chapters_menu():
    report = (
        "🚀 **ДНЕВНИК ЮНОГО КОСМОНАВТА**\n"
        "──────────────────────────\n"
        "**ОПИСАНИЕ МИССИИ:**\n"
        "Расследование инцидента на станции 'Авалон-7'. Тайны древнего мха, заговоры корпораций и поиск правды в глубинах космоса.\n\n"
        "📡 **АРХИВЫ ПАМЯТИ (ПЛАН ЭКСПЕДИЦИИ):**"
    )
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        tele_types.InlineKeyboardButton("✅ Глава 1: Протокол 'Эхо'", callback_data="game_start"),
        tele_types.InlineKeyboardButton("🪐 Глава 2: Тень Земли", callback_data="game2_start"),
        tele_types.InlineKeyboardButton("📡 Глава 3: Сигнал из пустоты", callback_data="game3_start"),
        
        # 🟢 ИСПРАВЛЕНО ЗДЕСЬ: Убрали СКОРО и поменяли callback_data
        tele_types.InlineKeyboardButton("☣️ Глава 4: Объект 'Зеро'", callback_data="game4_start"),
        tele_types.InlineKeyboardButton("🌌 Глава 5: Последний рубеж", callback_data="game5_start"),
        
        tele_types.InlineKeyboardButton("⬅️ Назад в Игровой отсек", callback_data="game_main_menu")
    )
    return report, kb
