import telebot
from datetime import datetime
from telebot import types as tele_types
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Док"
    current_node, timer_end = get_game_status(user_id)

    # 1. ПРОВЕРКА ТАЙМЕРА (Крафт или Обыск)
    if timer_end and datetime.now() < timer_end:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"🧪 Процесс идет... Осталось {mins} мин. Марти следит за приборами.", show_alert=True)
        return

    # 2. СТАРТ ИГРЫ: Пробуждение в бункере
    if call.data == "apoc_start":
        text = (f"☢️ **ПРОТОКОЛ: ЧИСТОЕ НЕБО**\n"
                f"──────────────────────────\n"
                f"Вы открываете глаза. В бункере пахнет озоном и старой пылью. Мигает красная лампа — основной генератор сдох.\n\n"
                f"Марти (той-пудель в маленьком тех-жилете) лижет вам руку и тихо ворчит. Его звуковой модуль выдает: 'Док... энергия 5%... если не починим панели на поверхности, фильтры воздуха отключатся через час'.\n\n"
                f"Ваш старый защитный костюм висит на манекене, но он весь в дырах после последней вылазки.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🛠 Осмотреть костюм", callback_data="apoc_n1_suit_inspect"),
            tele_types.InlineKeyboardButton("📦 Обыскать ящики в бункере", callback_data="apoc_n1_search_base")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "apoc_n1_base")

    # --- ЭТАП: ОСМОТР КОСТЮМА ---
    elif call.data == "apoc_n1_suit_inspect":
        # Проверяем ресурсы (условно: для починки нужно 2 ткани)
        has_cloth = current_node.count("res_cloth")
        
        text = (f"🛡 **ВЕРСТАК: ЗАЩИТНЫЙ КОСТЮМ**\n"
                f"──────────────────────────\n"
                f"Для герметизации нужно: **2 ед. ткани** и **1 фильтр**.\n"
                f"Ваши ресурсы: 📦 Ткань: {has_cloth}/2 | ☢️ Фильтры: 0/1\n\n"
                f"Марти: 'Без него на поверхности мы превратимся в светящиеся угли за 5 минут'.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        if has_cloth >= 2:
            kb.add(tele_types.InlineKeyboardButton("⚒ Начать починку (30 мин)", callback_data="apoc_craft_suit"))
        else:
            kb.add(tele_types.InlineKeyboardButton("🔍 Искать материалы", callback_data="apoc_n1_search_base"))
        
        kb.add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="apoc_start"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- ЭТАП: ПОИСК РЕСУРСОВ ---
    elif call.data == "apoc_n1_search_base":
        set_game_timer(user_id, 5) # Ищем 5 минут
        text = ("📦 **ПОИСК МАТЕРИАЛОВ**\n\n"
                "Вы переворачиваете ящики с инструментами. Марти залез под стеллаж и что-то там нашел.\n"
                "Нужно время, чтобы всё разобрать.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить добычу", callback_data="apoc_n1_search_result"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "apoc_n1_searching")

    elif call.data == "apoc_n1_search_result":
        # Добавляем ресурсы к строке прогресса
        update_game_progress(user_id, current_node + "_res_cloth_res_cloth") 
        text = ("✅ **УСПЕХ**\n\nНайдено: **2 ед. плотной ткани**. Теперь можно попробовать подлатать костюм!")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🛠 К верстаку", callback_data="apoc_n1_suit_inspect"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

def handle_craft(bot, call):
    user_id = call.from_user.id
    if "suit" in call.data:
        set_game_timer(user_id, 30)
        update_game_progress(user_id, "apoc_n1_suit_ready")
        bot.edit_message_text("⚒ **РАБОТА ПОШЛА**\n\nКостюм на верстаке. Швейная машинка стучит, клей сохнет. Зайдите через 30 минут.", call.message.chat.id, call.message.message_id)

def reset_game(bot, call):
    update_game_progress(call.from_user.id, "apoc_start")
    bot.answer_callback_query(call.id, "Симуляция перезапущена.")
    run_scenario(bot, call)
