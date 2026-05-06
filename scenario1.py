import telebot
from datetime import datetime
from telebot import types as tele_types
# Импортируем функции базы данных из вашего файла database.py
from database import get_game_status, update_game_progress, set_game_timer

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Пилот"
    
    # Получаем статус игрока
    current_node, timer_end = get_game_status(user_id)
    
    # 1. Проверка глобального таймера (общая для всех сцен)
    if timer_end and datetime.now() < timer_end:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"⏳ Марти занят. Будет готов через {mins} мин.", show_alert=True)
        return

    # 2. Навигация по сюжету
    if call.data == "game_start":
        text = (f"🛰 **БОРТОВОЙ ЖУРНАЛ: ЗАПИСЬ #1**\n\n"
                f"{username}, шлюз 'Авалона-7' встретил вас ледяным сквозняком. "
                f"Марти замер, его сенсоры сканируют темноту. Перед вами — разбитая панель управления и "
                f"ряд запертых шкафчиков экипажа.\n\n"
                "С чего начнете?")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🔍 Осмотреть панель", callback_data="game_node_panel"),
            tele_types.InlineKeyboardButton("📦 Вскрыть шкафчики", callback_data="game_node_closet")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_entry")

    elif call.data == "game_node_panel":
        set_game_timer(user_id, 10)
        text = ("⚙️ Вы коснулись проводов. Марти тут же выпустил манипулятор:\n\n"
                "— Хозяин, здесь зашифрованный протокол 'Эхо'. Мне нужно около **10 минут**, чтобы взломать систему. "
                "Пока я работаю, не отходите далеко.")
        kb = tele_types.InlineKeyboardMarkup()
        kb.add(tele_types.InlineKeyboardButton("⬅️ Вернуться на мостик", callback_data="game_back_to_profile"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "hacking_panel")

    # Сюда мы будем добавлять новые elif для шкафчиков, пергаментов и т.д.
