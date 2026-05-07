from telebot import types as tele_types

# 1. ГЛАВНОЕ МЕНЮ ИГР (Центральный хаб)
def get_main_games_menu():
    report = (
        "🌌 **ИГРОВОЙ ОТСЕК АКАДЕМИИ ОРИОН** 🌌\n"
        "──────────────────────────\n"
        "Здесь стирается грань между реальностью и тренировкой. Каждая симуляция — это проверка твоего интеллекта, "
        "смелости и умения принимать решения в критических ситуациях.\n\n"
        "📡 **СИСТЕМЫ ГОТОВЫ:** Выбери активную миссию из списка ниже и начни свое погружение. Прием!"
    )
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        tele_types.InlineKeyboardButton("🚀 Дневник юного космонавта", callback_data="game_select_diary"),
        tele_types.InlineKeyboardButton("🔒 [ДОСТУП ЗАКРЫТ: РАНГ КАПИТАН]", callback_data="game_locked_alert")
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
        # Будущие главы с пометкой "Скоро"
        tele_types.InlineKeyboardButton("📡 Глава 3: Сигнал из пустоты [СКОРО]", callback_data="game_soon_alert"),
        tele_types.InlineKeyboardButton("☣️ Глава 4: Объект 'Зеро' [СКОРО]", callback_data="game_soon_alert"),
        tele_types.InlineKeyboardButton("🌌 Глава 5: Последний рубеж [СКОРО]", callback_data="game_soon_alert"),
        
        tele_types.InlineKeyboardButton("⬅️ Назад в Игровой отсек", callback_data="game_main_menu")
    )
    return report, kb
