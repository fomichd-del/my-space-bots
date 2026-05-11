# Файл: game/main_router.py
from . import router as space_router  # Импорт роутера космоса (он в этой же папке)
from .game_apoc import router as apoc_router # Импорт роутера апокалипсиса (он в подпапке)

def handle_game_selection(bot, call):
    data = call.data
    
    if data.startswith('apoc_'):
        apoc_router.route_apoc(bot, call)
    elif data.startswith('game_'):
        space_router.route_game(bot, call)
    elif data == "hub_main_menu":
        show_hub_menu(bot, call)

def show_hub_menu(bot, call):
    from telebot import types
    text = (f"🖥 **ЦЕНТРАЛЬНЫЙ ТЕРМИНАЛ**\n\n"
            f"Док / Пилот, выберите симуляцию для погружения:")
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🚀 Дневник юного космонавта", callback_data="game_main_menu"),
        types.InlineKeyboardButton("☢️ Протокол: Чистое Небо", callback_data="apoc_start")
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
