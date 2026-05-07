from telebot import types as tele_types

# 1. ГЛАВНОЕ МЕНЮ ИГР
def get_main_games_menu():
    report = (
        "🎮 **ИГРОВОЙ ОТСЕК АКАДЕМИИ**\n\n"
        "Пилот, выбери симуляцию для погружения:"
    )
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        # 🟢 ДОБАВИЛИ game_ в начало
        tele_types.InlineKeyboardButton("🚀 Дневник юного космонавта", callback_data="game_select_diary"),
    )
    return report, kb

# 2. МЕНЮ ГЛАВ
def get_diary_chapters_menu():
    report = (
        "🚀 **ДНЕВНИК ЮНОГО КОСМОНАВТА**\n\n"
        "Выбери доступную часть:"
    )
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        tele_types.InlineKeyboardButton("📁 Глава 1: Протокол 'Эхо'", callback_data="game_start"),
        tele_types.InlineKeyboardButton("🪐 Глава 2: Тень Земли", callback_data="game2_start"),
        tele_types.InlineKeyboardButton("⬅️ Назад к списку игр", callback_data="game_main_menu")
    )
    return report, kb
