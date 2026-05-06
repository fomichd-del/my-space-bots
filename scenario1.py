# --- ВЕТКА: ВЗЯТЬ МЕДАЛЬОН (РИСК) ---
    elif call.data == "game_node_medalion":
        # Начисляем немного XP за смелость
        # add_xp(user_id, 2) # Можно вызвать функцию из базы, если нужно
        text = (f"🖐 Вы протягиваете руку и касаетесь холодного металла. В ту же секунду ваше зрение "
                f"вспыхивает белым светом. Тело пронзает слабый электрический разряд.\n\n"
                f"Прямо на сетчатке вашего глаза, поверх интерфейса шлема, начинают бежать кроваво-красные цифры:\n"
                f"📍 **СЕКТОР: 0-Г-13**\n"
                f"📍 **КООРДИНАТЫ: 42.0081 // -19.4402**\n\n"
                f"Вы слышите хриплый, прерывающийся шепот в динамиках: 'Не ищите нас... оно уже здесь'.\n\n"
                f"Марти подпрыгивает и толкает вас носом, приводя в чувство. Медальон в вашей руке "
                f"мгновенно почернел и превратился в бесполезный кусок пластика. "
                f"Но координаты теперь выжжены в вашей памяти.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🛰 Ввести данные в панель", callback_data="game_node_panel_with_coords"),
            tele_types.InlineKeyboardButton("🏠 Вернуться на мостик", callback_data="game_back_to_profile")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_coords_found")

    # --- ВЕТКА: МАРТИ ПРИНОСИТ (ОСТОРОЖНОСТЬ) ---
    elif call.data == "game_node_marty_bring":
        text = (f"🐕 Марти аккуратно подкрадывается к шкафчику и хватает медальон зубами. "
                f"Раздается короткий треск статики. Пес испуганно роняет вещь и отскакивает.\n\n"
                f"— Хозяин! — динамик Марти выдает помехи. — Мои системы зафиксировали "
                f"передачу пакета данных. Это навигационный маяк. Он транслирует точку назначения "
                f"глубоко внутри фиолетовой туманности.\n\n"
                f"Медальон перестал пульсировать. Похоже, он передал всё, что мог, и 'умер'.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🔍 Посмотреть, куда ведут данные", callback_data="game_node_panel_with_coords"),
            tele_types.InlineKeyboardButton("⬅️ Назад к панели", callback_data="game_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_marty_data")
