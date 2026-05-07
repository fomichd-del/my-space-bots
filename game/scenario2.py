import telebot
from datetime import datetime
from telebot import types as tele_types
# Импортируем функции базы данных
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Пилот"
    
    current_node, timer_end = get_game_status(user_id)
    
    # 1. Глобальная проверка таймера
    if timer_end and datetime.now() < timer_end:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"⏳ Марти анализирует данные. Готовность через {mins} мин.", show_alert=True)
        return

    # 2. УМНЫЙ СТАРТ: Точка сохранения для Главы 2
    if call.data == "game2_start":
        # Проверяем, есть ли уже прогресс именно во второй главе
        if current_node and current_node.startswith("ch2_") and current_node != "ch2_start":
            text = (f"🛰 **БОРТОВОЙ ЖУРНАЛ: ГЛАВА 2**\n\n"
                    f"{username}, системы восстановили последний сеанс связи.\n"
                    f"Желаете продолжить миссию или начать главу заново?")
            
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            
            # Маршрутизация точек сохранения
            if current_node == "ch2_hangar_hack":
                kb.add(tele_types.InlineKeyboardButton("🔄 Проверить статус взлома", callback_data="game2_check_hack"))
            elif current_node == "ch2_interrogation":
                kb.add(tele_types.InlineKeyboardButton("🚪 Войти в допросную", callback_data="game2_interrogation_room"))
            else:
                kb.add(tele_types.InlineKeyboardButton("🔄 Обновить статус", callback_data="game2_check_hack"))

            kb.add(tele_types.InlineKeyboardButton("♻️ Начать Главу 2 заново", callback_data="game2_reset"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

        # Вступление Главы 2
        text = (f"🛰 **БОРТОВОЙ ЖУРНАЛ: ГЛАВА 2 - ТЕНЬ ЗЕМЛИ**\n\n"
                f"Челнок тяжело стыкуется с орбитальной станцией 'Орион-Прайм'. "
                f"Вы едва успели снять шлем, как по громкой связи раздалось:\n\n"
                f"*«Пилот {username}, немедленно проследуйте в Отсек Безопасности. Ваш груз подлежит изъятию».*\n\n"
                f"Марти тихо зарычал. Его сканеры показывают, что вещи из Сектора Зеро излучают скрытый сигнал. "
                f"Нас ждут. И вряд ли с хорошими новостями.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🧳 Спрятать улики в тайнике Марти", callback_data="game2_hide_evidence"),
            tele_types.InlineKeyboardButton("🚶 Идти на допрос как есть", callback_data="game2_interrogation_room"),
            tele_types.InlineKeyboardButton("🛑 Сбросить прогресс", callback_data="game2_reset")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_start")

    elif call.data == "game2_reset":
        update_game_progress(user_id, "ch2_start")
        bot.answer_callback_query(call.id, "Журнал Главы 2 очищен.")
        call.data = "game2_start"
        run_scenario(bot, call)

    # --- ВЕТКА: СПРЯТАТЬ УЛИКИ (ТАЙМЕР 15 МИН) ---
    elif call.data == "game2_hide_evidence":
        set_game_timer(user_id, 15)
        text = ("⚙️ Вы перекладываете Золотую Ключ-карту и образцы в свинцовый контейнер внутри Марти.\n\n"
                "— Хозяин, мне нужно перекалибровать системы экранирования, чтобы обойти рамки "
                "Службы Безопасности. Процесс займет **15 минут**. Потяните время!")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🔄 Проверить готовность щитов", callback_data="game2_check_hack"))
        kb.add(tele_types.InlineKeyboardButton("🏠 На мостик", callback_data="game_back_to_profile"))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_hangar_hack")

    # --- РЕЗУЛЬТАТ: ЩИТЫ АКТИВИРОВАНЫ ---
    elif call.data == "game2_check_hack":
        text = (f"✅ **ЭКРАНИРОВАНИЕ УСПЕШНО**\n\n"
                f"Корпус Марти слегка нагрелся, но сигнал полностью заглушен. "
                f"Теперь вы готовы встретиться с офицерами Службы Безопасности.\n\n"
                f"Двери ангара с шипением открываются, на пороге стоят двое конвоиров.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🚪 Следовать за конвоем", callback_data="game2_interrogation_room"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_shields_up")

    # --- СЦЕНА ДОПРОСА ---
    elif call.data == "game2_interrogation_room":
        text = (f"🔦 Вас заводят в тесную комнату с ярким светом. За стальным столом сидит Офицер Веклер.\n\n"
                f"— Пилот {username}... Вы единственный, кто вернулся из Сектора Зеро в своем уме. "
                f"Расскажите для протокола: что вы там нашли? И главное — где капитан?\n\n"
                f"Марти сидит у ваших ног, готовый вмешаться, если потребуется.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🗣 Сказать правду про контрабанду пыли", callback_data="game2_truth"))
        kb.add(tele_types.InlineKeyboardButton("🤫 Солгать (Списать всё на сбой систем)", callback_data="game2_lie"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_interrogation")

    # Здесь мы будем дописывать продолжение...
