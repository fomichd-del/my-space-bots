# main_router.py
from game_space import router as space_router
from game_apoc import router as apoc_router

def handle_game_selection(bot, call):
    data = call.data
    
    # Распределяем потоки данных
    if data.startswith('apoc_'):
        apoc_router.route_apoc(bot, call)
    elif data.startswith('game_'):
        space_router.route_game(bot, call)
    
    # Главное меню выбора игр
    elif data == "hub_main_menu":
        show_hub_menu(bot, call)

def show_hub_menu(bot, call):
    from telebot import types
    text = (f"🖥 **ЦЕНТРАЛЬНЫЙ ТЕРМИНАЛ**\n\n"
            f"Пилот/Док, выберите доступную симуляцию:")
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🚀 Дневник юного космонавта", callback_data="game_main_menu"),
        types.InlineKeyboardButton("☢️ Протокол: Чистое Небо", callback_data="apoc_start")
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
