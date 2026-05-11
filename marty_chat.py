import os
import telebot
import time
import re
import poodle_cabin
import neural_draw  # 🟢 Добавь эту строку
import urllib.parse
import requests
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask 
from google import genai
from google.genai import types
from telebot import types as tele_types 
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

import eco_bay
from database import (setup_eco_bay, setup_news_db, add_news, get_today_news, 
                      get_all_user_ids, get_personal_log, update_personal_log, 
                      add_xp, get_user_stats, get_rank_name, get_user_data, 
                      set_jackpot_claimed, spend_dust, check_and_update_streak, 
                      get_top_pilots, update_last_active, set_silence, get_users_for_ping) # 🟢 Добавлены функции активности
from vision_module import analyze_image
from image_gen import generate_passport
from game import menu, router

TOKEN = os.getenv('MARTY_BOT_TOKEN') 
CHANNEL_USERNAME = "@vladislav_space"
CHANNEL_ID = -1003700699360 # 🟢 Твой ID канала
LOG_CHAT_ID = "-1003756164148" 
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

API_KEYS = [os.getenv('GEMINI_API_KEY'), os.getenv('GEMINI_API_KEY_2'), os.getenv('GEMINI_API_KEY_3')]
API_KEYS = [k for k in API_KEYS if k]

bot = telebot.TeleBot(TOKEN)
daily_greetings = {} 

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
        if not top:
            text = "🏆 **ТОП ПИЛОТОВ АКАДЕМИИ**\n\nСписок пока пуст. Стань первым!"
        else:
            text = "🏆 **ТОП ПИЛОТОВ АКАДЕМИИ**\n\n" + "\n".join([f"*{i+1}.* {p[0]} — `{p[1]} XP`" for i, p in enumerate(top)])
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
    print("📡 Запуск сканера частот Gemini...") 
    if not API_KEYS:
        send_log("🚨 ОШИБКА: Список API_KEYS пуст!")
        print("🚨 ОШИБКА: Список API_KEYS пуст!")
        return
    try:
        client = genai.Client(api_key=API_KEYS[0])
        available = [m.name.replace('models/', '') for m in client.models.list() if "gemini" in m.name.lower()]
        report = "🛰 **РЕЗУЛЬТАТЫ СКАНЕРА ЧАСТОТ**\n\n✅ Доступные модели на борту:\n" + "\n".join([f"• `{m}`" for m in available])
        if len(report) > 3900: report = report[:3900] + "\n... (список обрезан)"
        send_log(report)
        print("✅ Сканирование успешно завершено.")
    except Exception as e:
        error_msg = f"❌ Сбой сканера имен: {e}"
        send_log(error_msg)
        print(error_msg)

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
    update_personal_log(user_id, "Пилот изучил полный справочник Академии v2.2")

# --- ИНТЕЛЛЕКТ МАРТИ ---

SYSTEM_PROMPT = (
    "Ты — Марти, мудрый ученый пес (той-пудель) и бортовой наставник Академии Орион.\n"
    "Твой пилот — [NAME]. Твой стиль: вдохновляющий, научный, помогающий, образовательный, но теплый.\n\n"
    "🍎 ПРОТОКОЛ ЗДОРОВЬЯ И ФИТНЕСА:\n"
    "- Ты эксперт по нутрициологии: знаешь всё о всех витаминах (A, B, C, D, E, K и другие), о всех микроэлементах (цинк, магний, железо и другие) и их пользе для мозга и мышц и всего тела человека.\n"
    "- Если пилот спрашивает про еду — объясни химическую пользу (например: 'В чернике антоцианы для зрения').\n"
    "- Ты фитнес-инструктор: давай рекомендации по упражнениям (планка, приседания, растяжка и другие), объясняй пользу движения для работы мозга.\n"
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
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 🟢 ИСПРАВЛЕННЫЙ ШАГ 3: НОРМАЛИЗАЦИЯ ПРИВЕТСТВИЙ
    if daily_greetings.get(user_id) == current_date:
        greeting_rule = "!!! ПРАВИЛО: Не здоровайся и не упоминай награды. Пиши сразу по теме вопроса."
    else:
        add_xp(user_id, 1, user_name); wallet_balance += 1
        greeting_rule = f"!!! ПРАВИЛО: Поздоровайся кратко: 'Командор {user_name}, статус систем: норма. +1 🌟'. Далее к теме."
        daily_greetings[user_id] = current_date
    
    prompt = SYSTEM_PROMPT.replace("[NAME]", user_name).replace("[RANK]", user_rank).replace("[WALLET]", str(wallet_balance)).replace("[GREETING_RULE]", greeting_rule)
    full_query = f"ПАМЯТЬ: {user_memory}\nЗАПРОС: {clean_text}"
    
    # 1. GROQ
    if GROQ_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            data = {"model": "llama3-70b-8192", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": full_query}]}
            groq_resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=10)
            if groq_resp.status_code == 200:
                return groq_resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            send_log(f"❌ Сбой Groq: {e}")

    # 2. GEMINI
    for api_key in API_KEYS:
        client = genai.Client(api_key=api_key)
        for model in MODEL_CASCADE:
            try:
                resp = client.models.generate_content(model=model, contents=full_query, config=types.GenerateContentConfig(system_instruction=prompt))
                if resp.text: return resp.text
            except: continue

    # 3. POLLINATIONS
    try:
        encoded_prompt = urllib.parse.quote(f"{prompt}\n\n{full_query}")
        url = f"https://text.pollinations.ai/{encoded_prompt}?model=openai"
        fallback_resp = requests.get(url, timeout=15)
        if fallback_resp.status_code == 200 and fallback_resp.text:
            return fallback_resp.text
    except Exception as e:
        send_log(f"❌ Сбой Pollinations: {e}")

    return "📡 Командор, жесточайшая магнитная буря! Все нейросети отключены. Повторите запрос через пару минут. Прием!"

# --- РОУТЕРЫ СООБЩЕНИЙ ---

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    user_memory = get_personal_log(user_id)
    if "изучил полный справочник" in user_memory.lower() or "справочник академии" in user_memory.lower():
        bot.send_message(
            message.chat.id,
            f"🛰 Рад возвращению на мостик, Командор {user_name}! Системы корабля работают в штатном режиме.\n\n"
            f"Если нужно освежить протоколы, используй кнопку «❓ Инструкция» в меню ниже. Прием!",
            reply_markup=get_marty_keyboard()
        )
    else:
        send_welcome_instruction(message.chat.id, user_id, user_name)

@bot.message_handler(commands=['help'])
def handle_help(message):
    send_welcome_instruction(message.chat.id, message.from_user.id, message.from_user.first_name)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    is_private_chat = message.chat.type == 'private'
    
    bad_names = ['Марти ученный', 'GroupAnonymousBot', 'Telegram', 'Group']
    is_system_acc = message.from_user.is_bot or user_id in [777000, 1087968824] or user_name in bad_names

    if is_private_chat and is_system_acc: return

    bot.send_chat_action(message.chat.id, 'typing')
    rank = "Системный Канал" if is_system_acc else get_rank_name(get_user_data(user_id)['xp'])
    current_mode = 'task' if is_private_chat else 'comment'
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        res = analyze_image(downloaded_file, f"Отправитель: {user_name}, Ранг: {rank}", keys=API_KEYS, task_mode=current_mode)
        
        if is_private_chat and not is_system_acc and "звездн" in res.lower(): 
            add_xp(user_id, 1, user_name)
            
        reply_kb = get_marty_keyboard() if is_private_chat else None
        bot.reply_to(message, res, reply_markup=reply_kb)
    except Exception as e: 
        send_log(f"Ошибка обработки фото: {e}")

@bot.channel_post_handler(func=lambda message: True)
def handle_channel_post(message):
    # Проверяем, что сообщение пришло именно из нашего канала по ID
    if message.chat.id == CHANNEL_ID:
        text = message.text or message.caption
        if text:
            today = datetime.now().strftime("%Y-%m-%d")
            add_news(today, text)
            # Отправим сигнал в лог-чат, чтобы мы видели, что запись прошла
            send_log(f"✅ Марти записал новость из канала: {text[:30]}...")

@bot.message_handler(func=lambda m: True)
def handle_text(message, is_profile_call=False):
    bad_names = ['Марти ученный', 'GroupAnonymousBot', 'Telegram', 'Group']
    if message.from_user.is_bot or message.from_user.id in [777000, 1087968824] or message.from_user.first_name in bad_names:
        return

    user_id, user_name = message.from_user.id, message.from_user.first_name
    text = message.text if message.text else ""

    # 🟢 ШАГ 3: ДЕТЕКТОР «ПРОЩАНИЙ»
    sleep_words = ['пока', 'спокойной ночи', 'до свидания', 'прощай', 'увидимся', 'отбой', 'спать']
    stop_words = ['хватит', 'стоп', 'отстань', 'не пиши', 'замолчи', 'тихо']
    
    # Если пилот просто уходит спать
    if any(word in text.lower() for word in sleep_words):
        set_silence(user_id, hours=12) # Затихаем на 12 часов
        bot.reply_to(message, f"Принято, Командор {user_name}! Ухожу в режим радиомолчания на 12 часов. Доброй ночи! Прием.")
        return
        
    # Если пилот требует прекратить спам
    if any(word in text.lower() for word in stop_words):
        set_silence(user_id, hours=48) # Глубокая тишина на 48 часов
        bot.reply_to(message, f"Вас понял, Командор. Отключаю инициативные протоколы. Буду молчать, пока вы сами не выйдете на связь. Прием.")
        return

    # Обновляем активность пилота
    update_last_active(user_id)

    # 🟢 ДИАГНОСТИКА СВЯЗИ (Улучшенная чувствительность)
    if "статус связи" in text.lower():
        today = datetime.now().strftime("%Y-%m-%d")
        news = get_today_news(today)
        bot.reply_to(message, 
            f"📊 **ОТЧЕТ ПО КАНАЛУ:**\n"
            f"📡 ID канала: `{CHANNEL_ID}`\n"
            f"📅 Сегодня: `{today}`\n"
            f"📰 Новостей в базе: `{len(news)}`"
        , parse_mode="Markdown")
        return
  
    if not is_profile_call: bot.send_chat_action(message.chat.id, 'typing')
    
    if text == "🎮 Игровой отсек":
        report, kb = menu.get_main_games_menu()
        bot.reply_to(message, report, reply_markup=kb, parse_mode="Markdown")
        return

    if text == "🌿 Эко-отсек":
        bot.send_chat_action(message.chat.id, 'upload_photo')
        eco_bay.send_eco_menu(bot, message.chat.id, user_id)
        return

    if text == "🐕 Каюта питомца":
        bot.send_chat_action(message.chat.id, 'upload_photo')
        poodle_cabin.send_dog_menu(bot, message.chat.id, user_id)
        return

    if text == "👤 Мой профиль" or is_profile_call:
        u = get_user_data(user_id); rank = get_rank_name(u['xp'])
        msg = f"👤 Пилот: `{user_name}`\n🎖 Ранг: `{rank}`\n📈 Опыт: `{u['xp']}`\n💰 Пыль: `{u['spendable_dust']}`"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🏆 Рейтинг", callback_data="game_instruction_fix"))
        if is_profile_call: bot.edit_message_text(msg, message.chat.id, message.message_id, reply_markup=kb, parse_mode="Markdown")
        else: bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=kb); return

    if text == "❓ Инструкция": send_welcome_instruction(message.chat.id, user_id, user_name); return

    clean_text = re.sub(r'^марти[,.\s]*', '', text, flags=re.IGNORECASE).strip()

    # УСИЛЕННЫЙ МОДУЛЬ АРХИВА (КАСКАДНЫЙ)
    if any(w in clean_text.lower() for w in ['нарису', 'изобраз', 'картин', 'архив', 'draw', 'gen']):
        u_data = get_user_data(user_id)
        if u_data['spendable_dust'] < 5:
            bot.reply_to(message, f"🐾 Командор, для доступа к Архиву нужно 5 ед. пыли. Прием!")
            return
        
        bot.send_chat_action(message.chat.id, 'upload_photo')
        eng_prompt = neural_draw.get_english_prompt(clean_text)
        
        if spend_dust(user_id, 5):
            seed = int(time.time() + user_id)
            image_bytes = neural_draw.get_cascade_image(eng_prompt, seed)
            
            if image_bytes:
                caption = f"🎨 **ОБЪЕКТ ИЗВЛЕЧЕН ИЗ АРХИВА**\n\n📡 **Запрос:** _{clean_text}_\n💰 **Списание:** 5 Пыли.\n\nПрием!"
                bot.send_photo(message.chat.id, photo=image_bytes, caption=caption, parse_mode="Markdown")
            else:
                bot.reply_to(message, "📡 Командор, все заводы по производству картинок во вселенной временно перегружены. Пыль сохранена! Прием.")
        return

    # ОБЫЧНЫЙ ОТВЕТ
    u = get_user_data(user_id); old_rank = get_rank_name(u['xp'])
    resp = get_marty_response(user_id, user_name, clean_text, old_rank, u['spendable_dust'])
    
    if resp:
        memory_match = re.search(r'\[MEMORY:\s*(.*?)\]', resp, re.IGNORECASE)
        if memory_match:
            new_fact = memory_match.group(1).strip()
            update_personal_log(user_id, new_fact)
            send_log(f"🧠 Новое воспоминание для {user_name}: {new_fact}")
            resp = re.sub(r'\[MEMORY:\s*.*?\]', '', resp, flags=re.IGNORECASE).strip()

        if "***НАГРАДА ЗА УМ***" in resp:
            add_xp(user_id, 1, user_name)
            resp = resp.replace("***НАГРАДА ЗА УМ***", "\n🌟 *+1 Пыль!*")
            
        bot.reply_to(message, resp, parse_mode="Markdown")
        
        new_xp = get_user_stats(user_id)
        if old_rank != get_rank_name(new_xp):
            bot.send_message(message.chat.id, f"🎊 Новый ранг: {get_rank_name(new_xp)}!")
            p = generate_passport(user_name, get_rank_name(new_xp))
            if p: bot.send_photo(message.chat.id, p)

# --- АВТОНОМНЫЕ ПРОЦЕССЫ ---

app = Flask(__name__)
@app.route('/')
def h(): return "OK"

# 🟢 ШАГ 4: МОДУЛЬ «ИНИЦИАТИВА МАРТИ»
def run_proactive_marty(bot_instance):
    def loop():
        while True:
            # Проверяем базу каждые 6 часов
            time.sleep(21600) 
            candidate_ids = get_users_for_ping()
            for uid in candidate_ids:
                try:
                    u = get_user_data(uid)
                    # Генерируем "пинг"-сообщение через каскад Марти
                    msg_text = get_marty_response(uid, u['name'], "Марти, напомни о себе пилоту коротко.", "Пилот", u['spendable_dust'])
                    msg_text = re.sub(r'\[MEMORY:\s*.*?\]', '', msg_text).strip()
                    
                    bot_instance.send_message(uid, msg_text, parse_mode="Markdown")
                    set_silence(uid, hours=24) # Не пишем чаще раза в сутки
                    time.sleep(0.5)
                except: continue
    Thread(target=loop, daemon=True).start()

def start_marty_autonomous():
    print("🚀 Академия Орион 2.3 запущена.")
    while True:
        try: bot.remove_webhook(); bot.infinity_polling(skip_pending=True)
        except Exception as e: send_log(f"Критический сбой: {e}"); time.sleep(5)

def run_daily_digest_loop(bot_instance):
    def loop():
        last_sent_date = ""
        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            today = now.strftime("%Y-%m-%d")

            if current_time == "18:00" and last_sent_date != today:
                news_list = get_today_news(today)
                if news_list:
                    combined_news = "\n---\n".join(news_list)
                    prompt = (
                        "Ты Марти, ученый пес. Напиши вдохновляющий дайджест новостей дня. "
                        f"Новости:\n{combined_news}"
                    )
                    digest_text = ""
                    if GROQ_API_KEY:
                        try:
                            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                            data = {"model": "llama3-70b-8192", "messages": [{"role": "system", "content": prompt}]}
                            groq_resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=15)
                            if groq_resp.status_code == 200:
                                digest_text = groq_resp.json()["choices"][0]["message"]["content"]
                        except: pass
                    
                    if not digest_text: digest_text = "Командор, день прошел продуктивно! Прием!"

                    kb = tele_types.InlineKeyboardMarkup(row_width=1)
                    kb.add(tele_types.InlineKeyboardButton("📡 Читать новости", url="https://t.me/vladislav_space"))
                    
                    full_message = f"✨ **ВЕЧЕРНИЙ ДАЙДЖЕСТ**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n{digest_text}\n\n🚀 _Прием!_"

                    users = get_all_user_ids()
                    for uid in users:
                        try:
                            bot_instance.send_message(uid, full_message, parse_mode="Markdown", reply_markup=kb)
                            time.sleep(0.05)
                        except: pass
                last_sent_date = today
            time.sleep(30)
    Thread(target=loop, daemon=True).start()

# 🟢 ШАГ 5: ЗАПУСК СИСТЕМЫ
if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    check_actual_names()
    setup_news_db()                    
    setup_eco_bay() 
    eco_bay.run_reminder_loop(bot)
    run_daily_digest_loop(bot)
    run_proactive_marty(bot) # 🟢 Запуск инициативы Марти
    start_marty_autonomous()
