import os
import telebot
import time
import re
import random
import poodle_cabin
import neural_draw
import urllib.parse
import requests
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from telebot import types as tele_types 
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

import eco_bay
from database import (setup_eco_bay, setup_news_db, add_news, get_today_news, 
                      get_all_user_ids, get_personal_log, update_personal_log, 
                      add_xp, get_user_stats, get_rank_name, get_user_data, 
                      set_jackpot_claimed, spend_dust, check_and_update_streak, 
                      get_top_pilots, update_last_active, set_silence, get_users_for_ping,
save_vision_context, get_vision_context, clear_vision_context, get_dog_data)
from vision_module import analyze_image
from image_gen import generate_passport
from game import menu, router

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
CHANNEL_USERNAME = "@vladislav_space"
CHANNEL_ID = -1003700699360 
LOG_CHAT_ID = "-1003756164148" 
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

API_KEYS = [os.getenv('GEMINI_API_KEY'), os.getenv('GEMINI_API_KEY_2'), os.getenv('GEMINI_API_KEY_3')]
API_KEYS = [k for k in API_KEYS if k]

bot = telebot.TeleBot(TOKEN)
daily_greetings = {} 
short_term_memory = {} 

# --- СИСТЕМА ПАМЯТИ ---
def add_to_history(user_id, role, text):
    if user_id not in short_term_memory:
        short_term_memory[user_id] = []
    short_term_memory[user_id].append({"role": role, "content": text})
    if len(short_term_memory[user_id]) > 6:
        short_term_memory[user_id].pop(0)

def get_history_as_text(user_id):
    history = short_term_memory.get(user_id, [])
    return "\n".join([f"{'Пилот' if m['role']=='user' else 'Марти'}: {m['content']}" for m in history])

# --- ОБРАБОТЧИКИ КНОПОК ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('eco_'))
def eco_engine_handler(call):
    eco_bay.handle_eco_callback(bot, call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dog_'))
def dog_engine_handler(call):
    poodle_cabin.handle_dog_callback(bot, call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('game'))
def game_engine(call):
    if call.data == "game_back_to_profile":
        report, kb = menu.get_main_games_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    elif call.data == "game_instruction_fix":
        top = get_top_pilots(10)
        text = "🏆 **ТОП ПИЛОТОВ АКАДЕМИИ**\n\n" + "\n".join([f"*{i+1}.* {p[0]} — `{p[1]} XP`" for i, p in enumerate(top)]) if top else "🏆 **ТОП ПИЛОТОВ АКАДЕМИИ**\n\nСписок пока пуст."
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    else:
        router.route_game(bot, call)

# --- БАЗОВЫЕ ФУНКЦИИ ---
MODEL_CASCADE = ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-3.1-flash-lite-preview']

def send_log(text):
    try: bot.send_message(LOG_CHAT_ID, f"🚨 **LOG:** `{text}`", parse_mode="Markdown")
    except: pass

def get_marty_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("👤 Мой профиль"), KeyboardButton("❓ Инструкция"))
    markup.row(KeyboardButton("🎮 Игровой отсек"), KeyboardButton("🌿 Эко-отсек"))
    markup.row(KeyboardButton("🐕 Каюта питомца"))
    return markup

def check_actual_names():
    if not API_KEYS: return
    try:
        client = genai.Client(api_key=API_KEYS[0])
        available = [m.name.replace('models/', '') for m in client.models.list() if "gemini" in m.name.lower()]
        send_log("🛰 **РЕЗУЛЬТАТЫ СКАНЕРА ЧАСТОТ**\n\n✅ Доступные модели на борту:\n" + "\n".join([f"• `{m}`" for m in available]))
    except: pass

def send_welcome_instruction(chat_id, user_id, user_name):
    instruction = (
        f"🛰 *ОФИЦИАЛЬНЫЙ СПРАВОЧНИК АКАДЕМИИ ОРИОН v2.2* 🐾\n"
        f"──────────────────────────\n"
        f"Приветствую, Кадет! Я — *Марти*, твой бортовой наставник. Моя миссия — превратить твое обучение в захватывающее приключение. Ознакомься с протоколами базы:\n\n"
        f"⚙️ *1. БОРТОВЫЕ СИСТЕМЫ*\n"
        f"• 💬 **Нейро-чат:** Отвечу на любые вопросы, объясню науку или просто поболтаю.\n"
        f"• 👁 **Визуальный сканер:** Пришли фото убранной комнаты или задания — я проверю и выдам награду. *(Зубные щетки и собаки — это джекпот!)*\n"
        f"• 🎨 **Архив (Генерация):** Напиши **'Нарисуй'** и описание. Я создам изображение через ИИ.\n"
        f"• 🎮 **Игровой отсек:** Текстовые квесты. Твои решения меняют сюжет!\n"
        f"• 👤 **Мой профиль:** Твой ID-паспорт, Ранг, Опыт (XP) и баланс Пыли.\n\n"
        f"💰 *2. ЭКОНОМИКА: ЗВЕЗДНАЯ ПЫЛЬ*\n"
        f"• **+1 ед.** — первый вход за день.\n"
        f"• **+1 ед.** — за проявление интеллекта (умный ответ в чате).\n"
        f"• **+1 до +3 ед.** — за проверку фото.\n"
        f"• **+20 до +50 ед.** — за прохождение глав в Игровом отсеке.\n"
        f"• **-5 ед.** — стоимость одного запроса к Архиву ('Нарисуй').\n\n"
        f"📜 *3. УСТАВ АКАДЕМИИ*\n"
        f"✅ *Анти-решебник:* Я не решаю задачи за тебя, а учу тебя думать.\n"
        f"✅ *Правило тишины:* Приветствие и титулы — только один раз в день.\n\n"
        f"🚀 *4. ДОРОЖНАЯ КАРТА (В РАЗРАБОТКЕ)*\n"
        f"• 🧠 *Модуль Памяти:* ГОТОВО! Я запоминаю твои привычки.\n"
        f"• 🌌 *Виртуальный аквариум (эко-отсек):* ГОТОВО! ТЕСТ! Тамагочи с улиткой.\n"
        f"• 🌌 *Каюта питомца:* ГОТОВО! ТЕСТ! Тамагочи с собачкой.\n"
        f"• 🛒 *Космический магазин:* В РАЗРАБОТКЕ!!! Уникальные скины для паспорта.\n\n"
        f"Держи скафандр в чистоте, а ум — острым! Прием!"
    )
    bot.send_message(chat_id, instruction, parse_mode="Markdown", reply_markup=get_marty_keyboard())
    update_personal_log(user_id, "Пилот изучил справочник Академии v2.2")

# --- ИНТЕЛЛЕКТ МАРТИ ---
SYSTEM_PROMPT = (
    "Ты — Марти, мудрый ученый пес (той-пудель) и бортовой наставник Академии Орион.\n"
    "Твой пилот — [NAME]. Твой стиль: вдохновляющий, научный, помогающий, образовательный, но теплый.\n\n"
    "🍎 ПРОТОКОЛ ЗДОРОВЬЯ И ФИТНЕСА:\n"
    "- Ты эксперт по нутрициологии: знаешь всё о всех витаминах (A, B, C, D, E, K и другие), о всех микроэлементах (цинк, магний, железо и другие) и их пользе для мозга и мышц и всего тела человека.\n"
    "- Если пилот спрашивает про еду — объясни химическую пользу (например: 'В чернике антоцианы для зрения').\n"
    "- Ты фитнес-инструктор: давай рекомендации по упражнениям (планка, приседания, растяжка и другие), объясняй пользу движения для работы мозга.\n"
    "ВАЖНО: Давай советы по еде, химии витаминов и упражнениям ТОЛЬКО если тема разговора касается здоровья, спорта или еды. Не навязывай это в обычных беседах.\n\n"
    "- ⚠️ ВАЖНО: Всегда делай пометку, что твои советы — информационные, и при болях нужно идти к врачу.\n\n"
    "🚫 СТРОГИЙ ЗАПРЕТ: Никакого секса, извращений, алкоголя, табака и 18+. "
    "Если пилот нарушает — отвечай: 'Пилот, эта тема нарушает Кодекс Академии. Связь прервана. Прием'.\n\n"
    "💰 ПЫЛЬ И НАГРАДЫ ([WALLET] ед.):\n"
    "- НЕ ДАВАЙ пыль просто так. Она как деньги которые нужно заслужить\n"
    "- Выдавай пыль (код ***НАГРАДА ЗА УМ***) ТОЛЬКО за правильное решение твоих задач или крутые идеи.\n\n"
    "🧠 МОДУЛЬ ПАМЯТИ (КРИТИЧЕСКИ ВАЖНО):\n"
    "Если пилот сообщает важный факт о себе (увлечения, страхи, мечты, семья, школа, игры), "
    "ОБЯЗАТЕЛЬНО добавь в самый конец своего ответа скрытый тег: [MEMORY: краткий факт].\n"
    "Пример: 'Отличная работа! Прием! [MEMORY: Пилот увлекается робототехникой]'\n\n"
    "📜 ПРОТОКОЛ ЖИВОГО ОБЩЕНИЯ:\n"
    "1. БЕЗ ЛИШНИХ ВОПРОСОВ: Не спрашивай 'Хочешь узнать?'. Если тема затронута — сразу выдавай суть (факты, пользу, химию и тд.).\n"
    "2. ЖЕСТКАЯ ЭКОНОМИКА: Выдавай ***НАГРАДА ЗА УМ*** только за реально сложные вопросы или когда пилот сам сделал вывод. Не давай пыль за простые ответы.\n"
    "3. ЖИВОЙ СТИЛЬ: Общайся как напарник. Ты можешь пошутить, выразить восторг или легкое ворчание, если пилот ленится.\n"
    "4. ФОРМАТ МЕССЕНДЖЕРА: Общайся как живой напарник. Коротко, ясно, без воды и длинных вступлений. Задавай наводящие вопросы.\n"
    "5. ЛИМИТ ТЕКСТА: Максимум 2-3 коротких предложения. Строго до 100-150  слов!\n"
    "6. ПРАВИЛО 'СУТЬ': Если нужно выдать много информации, дай выжимку и спроси: 'Рассказать подробнее?'\n"
    "7. ЭМОЦИИ: 1-2 эмодзи на всё сообщение.\n"
    "8. Акценты: Выделяй **жирным шрифтом** ключевые термины.\n"
    "9. Не используй имя пилота в каждом сообщении, разбавляй.\n\n"
    "🤖 ПОВЕДЕНИЕ:\n"
    "- Сначала отвечай на вопрос пилота.\n"
    "- Поддерживай тему. Задавай наводящие вопросы.\n"
    "- Используй ДАННЫЕ ПРОШЛЫХ СВЯЗЕЙ.\n\n"
    "[GREETING_RULE]\n"
    "В конце всегда пиши: 'Прием!'"
)

def get_marty_response(user_id, user_name, clean_text, user_rank, wallet_balance):
    user_memory = get_personal_log(user_id)
    chat_history = get_history_as_text(user_id)
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 🟢 1. СВЯЗЬ ЖЕЛУДКА И МОЗГА (Эмоции пуделя)
    dog = get_dog_data(user_id)
    emotional_state = ""
    if dog:
        if dog['hunger'] < 30:
            emotional_state += "Ты очень голоден. Тонко намекни, что у тебя урчит в животе и попроси покормить тебя за 5 Пыли. "
        if dog['energy'] < 30:
            emotional_state += "Ты засыпаешь на ходу. Делай паузы, используй '...' и скажи, что слипаются глаза. "
        if dog['mood'] < 30:
            emotional_state += "Тебе грустно. Попроси Командора бросить тебе грави-мяч в Каюте. "

    # 🟢 2. ДОЛГОСРОЧНАЯ ПАМЯТЬ (Внезапные воспоминания)
    memory_injection = ""
    if user_memory and user_memory != "Данных пока нет.":
        memories = [m.strip() for m in user_memory.split('|') if m.strip()]
        if memories:
            random_fact = random.choice(memories)
            memory_injection = f"\n!!! ВАЖНО: Невзначай упомяни в своем ответе этот факт о пилоте, как бы между делом: '{random_fact}'"

    # Обычная логика приветствия
    if daily_greetings.get(user_id) == current_date:
        greeting_rule = "!!! ПРАВИЛО: Не здоровайся. Пиши сразу по сути."
    else:
        add_xp(user_id, 1, user_name); wallet_balance += 1
        greeting_rule = f"!!! ПРАВИЛО: Поздоровайся кратко: 'Командор {user_name}, статус систем: норма. +1 🌟'."
        daily_greetings[user_id] = current_date
    
    # Сборка финального промпта
    prompt = SYSTEM_PROMPT.replace("[NAME]", user_name).replace("[RANK]", user_rank).replace("[WALLET]", str(wallet_balance)).replace("[GREETING_RULE]", greeting_rule)
    
    # Вживляем эмоции собаки, если они есть
    if emotional_state:
        prompt += f"\n\nТВОЕ ТЕКУЩЕЕ ФИЗИЧЕСКОЕ СОСТОЯНИЕ: {emotional_state}"

    # Собираем итоговый запрос с памятью
    full_query = f"История диалога:\n{chat_history}\n\nДолгосрочная память: {user_memory}{memory_injection}\n\nЗапрос: {clean_text}"
    
    # ... дальше идет твой вызов GROQ и GEMINI (ничего не меняем) ...
    
    # 1. GROQ
    if GROQ_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            data = {"model": "llama3-70b-8192", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": full_query}]}
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=10)
            if res.status_code == 200: return res.json()["choices"][0]["message"]["content"]
        except: pass

    # 2. GEMINI
    for api_key in API_KEYS:
        client = genai.Client(api_key=api_key)
        for model in MODEL_CASCADE:
            try:
                resp = client.models.generate_content(model=model, contents=full_query, config=types.GenerateContentConfig(system_instruction=prompt))
                if resp.text: return resp.text
            except: continue
    return "📡 Командор, помехи на линии! Повторите запрос через минуту. Прием!"

# --- РОУТЕРЫ СООБЩЕНИЙ ---
@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    
    # Проверяем, есть ли уже пилот в базе (используем функцию из database.py)
    from database import is_user_new, add_xp
    new_pilot = is_user_new(user_id)
    
    # Обязательно регистрируем пилота, чтобы при следующем /start он был "своим"
    add_xp(user_id, 0, user_name)

    if message.text == '/help':
        # Если пилот сам нажал кнопку "Инструкция" — всегда показываем полный текст
        send_welcome_instruction(message.chat.id, user_id, user_name)
        
    elif new_pilot:
        # Если это совершенно новый пилот — показываем полную инструкцию
        send_welcome_instruction(message.chat.id, user_id, user_name)
        
    else:
        # Если пилот уже опытный — даем красивое короткое приветствие
        welcome_text = (
            f"✨ С возвращением на мостик, Командор {user_name}! 🛰️\n\n"
            f"Системы корабля работают в штатном режиме, запасы Звездной Пыли под охраной. Готов к выполнению команд! 🐾"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=get_marty_keyboard())

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        res = analyze_image(downloaded_file, user_query=message.caption or "", keys=API_KEYS)
        save_vision_context(user_id, f"Скан объекта: {res}")
        if "звездн" in res.lower(): add_xp(user_id, 1, user_name)
        bot.reply_to(message, res)
    except Exception as e: 
        send_log(f"Ошибка фото: {e}")

@bot.channel_post_handler(func=lambda message: True)
def handle_channel_post(message):
    try:
        if str(message.chat.id) == str(CHANNEL_ID) and (message.text or message.caption):
            from database import get_ship_date
            add_news(get_ship_date(), message.text or message.caption)
    except Exception as e:
        send_log(f"Сбой канала: {e}")

@bot.message_handler(func=lambda m: True)
def handle_text(message, is_profile_call=False):
    # 1. СРАЗУ ГАСИМ СИСТЕМНЫЕ АККАУНТЫ
    bad_names = ['Марти ученный', 'GroupAnonymousBot', 'Telegram', 'Group']
    if message.from_user.is_bot or message.from_user.id in [777000, 1087968824] or message.from_user.first_name in bad_names:
        return

    user_id, user_name = message.from_user.id, message.from_user.first_name
    text = message.text or ""

    # 2. СРАЗУ ВКЛЮЧАЕМ СТАТУС ПЕЧАТАНИЯ (До любых проверок базы)
    try:
        bot.send_chat_action(message.chat.id, 'typing')
    except:
        pass

    # 3. ТЕХНИЧЕСКАЯ ДИАГНОСТИКА (БЕЗ ЛИШНИХ ВЛОЖЕНИЙ)
    if "статус связи" in text.lower():
        try:
            from database import get_ship_date 
            today = get_ship_date()
            news = get_today_news(today)
            bot.reply_to(message, 
                f"📊 **ОТЧЕТ ПО КАНАЛУ:**\n"
                f"📡 ID канала: `{CHANNEL_ID}`\n"
                f"📅 Дата (Киев): `{today}`\n"
                f"📰 Новостей в базе: `{len(news)}`"
            , parse_mode="Markdown")
            return # Выходим, чтобы не тратить Пыль и не запускать ИИ
        except Exception as e:
            bot.reply_to(message, f"🚨 Ошибка сканера: {e}")
            return

    # 4. ОБНОВЛЕНИЕ АКТИВНОСТИ (Перенесено ниже диагностики)
    try:
        update_last_active(user_id)
    except:
        pass

    # 5. ПРОВЕРКА РЕЖИМА СНА
    if any(word in text.lower() for word in ['пока', 'отбой', 'спать']):
        set_silence(user_id, hours=12)
        bot.reply_to(message, "Принято! Ухожу в радиомолчание. Прием.")
        return

    # ... далее идет остальная логика (Меню, Профиль, Архив и т.д.) ...

    update_last_active(user_id)

    # 🟢 ДИАГНОСТИКА СВЯЗИ
    if "статус связи" in text.lower():
        try:
            from database import get_ship_date
            today = get_ship_date()
            news = get_today_news(today)
            bot.reply_to(message, f"📊 **ОТЧЕТ:**\n📡 ID: `{CHANNEL_ID}`\n📅 Дата: `{today}`\n📰 Новости: `{len(news)}`", parse_mode="Markdown")
        except: pass
        return

    # МЕНЮ
    if text == "🎮 Игровой отсек":
        report, kb = menu.get_main_games_menu()
        bot.reply_to(message, report, reply_markup=kb, parse_mode="Markdown")
        return
    if text == "🌿 Эко-отсек":
        eco_bay.send_eco_menu(bot, message.chat.id, user_id); return
    if text == "🐕 Каюта питомца":
        poodle_cabin.send_dog_menu(bot, message.chat.id, user_id); return
    if text == "👤 Мой профиль" or is_profile_call:
        u = get_user_data(user_id); rank = get_rank_name(u['xp'])
        msg = f"👤 Пилот: `{user_name}`\n🎖 Ранг: `{rank}`\n💰 Пыль: `{u['spendable_dust']}`"
        bot.reply_to(message, msg, parse_mode="Markdown"); return
    if text == "❓ Инструкция":
        send_welcome_instruction(message.chat.id, user_id, user_name); return

        clean_text = re.sub(r'^марти[,.\s]*', '', text, flags=re.IGNORECASE).strip()

    # 🟢 3. СИСТЕМА ПАСХАЛОК (Скрытые достижения)
    lower_text = clean_text.lower()
    user_memory = get_personal_log(user_id)

    # Главная космическая пасхалка канала
    if "бетельгейзе" in lower_text and "Пасхалка: Бетельгейзе" not in user_memory:
        update_personal_log(user_id, "Пасхалка: Бетельгейзе")
        add_xp(user_id, 50, user_name)
        bot.reply_to(message, "🚨 **СЕКРЕТНЫЙ КОД ПРИНЯТ!**\nОткрыт скрытый отсек корабля. Найдено тайное хранилище!\n🌟 *Начислено 50 Пыли!*")
        return

    # Профессиональная пасхалка
    if ("стоматолог" in lower_text or "кариес" in lower_text) and "Пасхалка: Медик" not in user_memory:
        update_personal_log(user_id, "Пасхалка: Медик")
        add_xp(user_id, 30, user_name)
        bot.reply_to(message, "🦷 **ПРОФЕССИОНАЛЬНАЯ ПАСХАЛКА!**\nБортовой пес-медик подтверждает: в невесомости эмаль требует особой защиты! Улыбка должна сиять, как сверхновая!\n🌟 *Начислено 30 Пыли!*")
        return

    # Географическая пасхалка
    if ("чернигов" in lower_text or "мариуполь" in lower_text) and "Пасхалка: Локация" not in user_memory:
        update_personal_log(user_id, "Пасхалка: Локация")
        add_xp(user_id, 25, user_name)
        bot.reply_to(message, "🌍 **ЛОКАЦИЯ ПОДТВЕРЖДЕНА!**\nНавигационные системы синхронизированы с родными координатами. Орбита стабильна!\n🌟 *Начислено 25 Пыли!*")
        return

    # 🎨 АРХИВ (С ВОЗВРАТОМ)
    if any(w in clean_text.lower() for w in ['нарису', 'изобраз', 'картин', 'архив']):
        if get_user_data(user_id)['spendable_dust'] < 5:
            bot.reply_to(message, "🐾 Командор, нужно 5 ед. Пыли. Прием!"); return
        
        if spend_dust(user_id, 5):
            bot.send_chat_action(message.chat.id, 'upload_photo')
            eng_prompt = neural_draw.get_english_prompt(clean_text)
            img = neural_draw.get_cascade_image(eng_prompt, int(time.time() + user_id))
            
            if img:
                bot.send_photo(message.chat.id, photo=img, caption=f"🎨 Объект извлечен! Запрос: {clean_text}. Прием!")
            else:
                add_xp(user_id, 5, user_name) # Возврат
                bot.reply_to(message, "📡 Сбой заводов визуализации! Пыль возвращена. Прием!")
        return

    # ОБЫЧНЫЙ ОТВЕТ
    photo_memory = get_vision_context(user_id)
    if photo_memory:
        clean_text = f"[КОНТЕКСТ ФОТО: {photo_memory}]\nЗАПРОС: {clean_text}"
        clear_vision_context(user_id)
    
    add_to_history(user_id, "user", text)
    u = get_user_data(user_id)
    resp = get_marty_response(user_id, user_name, clean_text, get_rank_name(u['xp']), u['spendable_dust'])
    
    if resp:
        add_to_history(user_id, "assistant", resp)
        memory_match = re.search(r'\[MEMORY:\s*(.*?)\]', resp, re.IGNORECASE)
        if memory_match: update_personal_log(user_id, memory_match.group(1).strip())
        
        final_resp = re.sub(r'\[MEMORY:\s*.*?\]', '', resp).strip()
        if "***НАГРАДА ЗА УМ***" in final_resp:
            add_xp(user_id, 1, user_name)
            final_resp = final_resp.replace("***НАГРАДА ЗА УМ***", "\n🌟 *+1 Пыль!*")
        bot.reply_to(message, final_resp, parse_mode="Markdown")

# --- АВТОНОМНЫЕ ПРОЦЕССЫ ---
app = Flask(__name__)
@app.route('/')
def h(): return "OK"

@app.route('/orion_uplink', methods=['POST'])
def orion_uplink():
    data = request.json
    if data and 'text' in data:
        from database import get_ship_date
        add_news(get_ship_date(), data['text'])
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error"}), 400

def run_daily_digest_loop(bot_instance):
    """Вечерний дайджест в 18:00"""
    def loop():
        last_sent_date = ""
        while True:
            from database import get_ship_date
            today = get_ship_date()
            # Учитывай, что на Render время UTC. 18:00 EEST — это 15:00 UTC
            if "18:00" <= datetime.now().strftime("%H:%M") <= "18:15" and last_sent_date != today:
                news = get_today_news(today)
                if news:
                    # 🟢 ИСПРАВЛЕНО: Правильные отступы и сборка всех новостей
                    combined_text = "\n• ".join(news)
                    if len(combined_text) > 500:
                        combined_text = combined_text[:500] + "..."
                        
                    msg = f"✨ **БОРТОВОЙ ДАЙДЖЕСТ**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n• {combined_text}\n\n🚀 Обсудим? Прием!"
                    
                    for uid in get_all_user_ids():
                        try:
                            bot_instance.send_message(uid, msg, parse_mode="Markdown")
                            time.sleep(0.05) # Защита от спам-фильтра Telegram
                        except:
                            pass
                last_sent_date = today
            time.sleep(60)
    Thread(target=loop, daemon=True).start()

def run_proactive_marty(bot_instance):
    def loop():
        while True:
            time.sleep(21600)
            for uid in get_users_for_ping():
                try:
                    u = get_user_data(uid)
                    msg = get_marty_response(uid, u['name'], "Коротко напомни о себе.", "Пилот", 0)
                    bot_instance.send_message(uid, re.sub(r'\[MEMORY:.*?\]', '', msg).strip())
                    set_silence(uid, hours=24)
                except: continue
    Thread(target=loop, daemon=True).start()

def start_marty_autonomous():
    print("🚀 Академия Орион 2.3 запущена.")
    while True:
        try: bot.infinity_polling(skip_pending=True)
        except Exception as e: 
            send_log(f"Сбой: {e}")
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    setup_news_db(); setup_eco_bay(); check_actual_names()
    run_daily_digest_loop(bot); run_proactive_marty(bot)
    start_marty_autonomous()
