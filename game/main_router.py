# Файл: game/main_router.py
from . import router as space_router  
from .game_apoc import router as apoc_router 

def handle_game_selection(bot, call):
    data = call.data
    
    if data.startswith('apoc_'):
        # 🟢 ИСПРАВЛЕНО: Если это вызов меню, обрабатываем его корректно
        if data == "apoc_menu":
            from . import menu
            report, kb = menu.get_apoc_chapters_menu()
            bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        else:
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
        # 🟢 ИСПРАВЛЕНО: callback_data изменена с apoc_start на apoc_menu
        types.InlineKeyboardButton("☢️ Протокол: Чистое Небо", callback_data="apoc_menu")
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
