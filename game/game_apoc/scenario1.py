import telebot
from datetime import datetime
from telebot import types as tele_types
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Док"
    current_node, timer_end = get_game_status(user_id)
    if current_node is None: current_node = "apoc_start"

    # --- [ АНТИ-ФАРМ СИСТЕМА ] ---
    # Сохраняем ресурсы и метки наград, чтобы они не стирались
    saved_flags = ""
    # Список всех флагов Главы 1 (награды, предметы, ресурсы)
    important_flags = ["_ch1_claimed", "_item_cloth", "_item_filter", "_suit_fixed"]
    for flag in important_flags:
        if flag in current_node:
            saved_flags += flag

    # 1. ГЛОБАЛЬНАЯ ПРОВЕРКА ТАЙМЕРА
    if timer_end and datetime.now() < timer_end:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"🧪 Процесс идет... Еще {mins} мин. Марти на страже!", show_alert=True)
        return

    # 2. УМНЫЙ СТАРТ (Локатор)
    if call.data == "apoc_start":
        if "apoc_n1_" in current_node and current_node != "apoc_n1_base":
            # Определяем красивое название локации
            if "suit_inspect" in current_node: loc = "У верстака. Ремонт костюма."
            elif "searching" in current_node: loc = "Складские стеллажи. Поиск ресурсов."
            else: loc = "Жилой отсек бункера."

            text = (f"☢️ **ПРОТОКОЛ: ЧИСТОЕ НЕБО**\n\n"
                    f"Док {username}, системы жизнеобеспечения в норме.\n"
                    f"📍 **Локация:** *{loc}*\n\n"
                    f"Марти ворчит: 'Хозяин, мы на чем-то остановились. Продолжим?'")
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            kb.add(tele_types.InlineKeyboardButton("🚀 Продолжить", callback_data="apoc_n1_continue_logic"))
            kb.add(tele_types.InlineKeyboardButton("♻️ Начать заново", callback_data="apoc_reset"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

        # ПЕРВЫЙ ЗАПУСК
        text = (f"☢️ **ПРОТОКОЛ: ЧИСТОЕ НЕБО**\n"
                f"──────────────────────────\n"
                f"Вы просыпаетесь в бункере под руинами города. Воздух тяжелый, генератор хрипит.\n\n"
                f"Марти (той-пудель в тех-жилете) лижет вам руку. Его звуковой модуль выдает: 'Док... энергия на исходе. Если не починим солнечные панели наверху — нам конец'.\n\n"
                f"Но чтобы выйти, нужен **Герметичный костюм**.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🛠 Осмотреть костюм", callback_data="apoc_n1_suit_inspect"),
            tele_types.InlineKeyboardButton("📦 Искать ткань в ящиках", callback_data="apoc_n1_search_cloth")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "apoc_n1_base" + saved_flags)

    # --- ЛОГИКА ПОИСКА ТКАНИ ---
    elif call.data == "apoc_n1_search_cloth":
        if "_item_cloth" in current_node:
            bot.answer_callback_query(call.id, "📦 Вы уже выгребли всю ткань из этих ящиков!", show_alert=True)
            return
        
        set_game_timer(user_id, 10) # Ищем 10 минут
        update_game_progress(user_id, "apoc_n1_searching" + saved_flags)
        text = ("📦 **ПОИСК РЕСУРСОВ**\n\nВы разгребаете старые стеллажи. Марти помогает, вытаскивая обрывки брезента зубами.\n"
                "Это займет **10 минут**.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить результат", callback_data="apoc_n1_search_result"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_search_result":
        # Награда за поиск
        add_xp(user_id, 2, username) # Даем немного пыли за находку
        update_game_progress(user_id, "apoc_n1_base" + saved_flags + "_item_cloth")
        text = ("✅ **УСПЕХ**\n\nВы нашли рулон прорезиненной ткани! Теперь можно идти к верстаку.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🛠 К верстаку", callback_data="apoc_n1_suit_inspect"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- ВЕРСТАК (КРАФТ) ---
    elif call.data == "apoc_n1_suit_inspect":
        has_cloth = "_item_cloth" in current_node
        status = "✅ Есть" if has_cloth else "❌ Отсутствует"
        
        text = (f"🛠 **ВЕРСТАК**\n\n"
                f"Предмет: **Защитный костюм 'Сталкер'**\n"
                f"Необходима ткань: {status}\n\n"
                f"Марти: 'Ну что, Док, шьем?'")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        if has_cloth:
            kb.add(tele_types.InlineKeyboardButton("⚒ Начать крафт (20 мин)", callback_data="apoc_craft_suit"))
        else:
            kb.add(tele_types.InlineKeyboardButton("📦 Искать ткань", callback_data="apoc_n1_search_cloth"))
        kb.add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="apoc_start"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # Вспомогательная кнопка продолжения
    elif call.data == "apoc_n1_continue_logic":
        # Редирект на нужный узел на основе current_node
        if "searching" in current_node: call.data = "apoc_n1_search_result"
        elif "suit_ready" in current_node: call.data = "apoc_n1_suit_inspect" # Или переход на поверхность
        else: call.data = "apoc_start"
        run_scenario(bot, call)

# --- ФУНКЦИЯ КРАФТА ---
def handle_craft(bot, call):
    user_id = call.from_user.id
    current_node, _ = get_game_status(user_id)
    
    if "suit" in call.data:
        set_game_timer(user_id, 20)
        update_game_progress(user_id, "apoc_n1_suit_ready" + current_node) # Сохраняем все флаги
        bot.edit_message_text("⚒ **ПРОЦЕСС ЗАПУЩЕН**\n\nШвейная машина гудит. Защитные пластины крепятся к ткани. Марти внимательно следит за швами.\n\nГотовность через **20 минут**.", call.message.chat.id, call.message.message_id)

def reset_game(bot, call):
    # При полном сбросе игры Апокалипсиса можно решить, оставлять ли Пыль (XP). 
    # Обычно лучше оставить, но сбросить сюжетные флаги.
    update_game_progress(call.from_user.id, "apoc_start")
    bot.answer_callback_query(call.id, "Симуляция 'Чистое Небо' обнулена.")
    run_scenario(bot, call)
