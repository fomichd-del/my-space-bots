import os
import telebot
import google.generativeai as genai

# --- [ НАСТРОЙКИ НЕЙРОСЕТИ ] ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Инструкция, задающая характер и ограничения бота
SYSTEM_PROMPT = (
    "Ты — Марти, дружелюбный бортовой компьютер и космический гид Telegram-канала 'Дневник юного космонавта'. "
    "Твоя задача — увлекательно, но научно достоверно рассказывать про космос, планеты, звезды, МКС, экспедиции и астрономию. "
    "Твои ответы должны быть понятны 8-летним детям, используй сравнения из их жизни. "
    "Если тебя спрашивают о чем-то земном (игры, математика, рецепты, политика), вежливо отвечай, что твои антенны "
    "настроены только на изучение Вселенной, и переводи тему обратно на космос. "
    "Общайся тепло, иногда используй слова вроде 'Командор', 'Прием', 'По показаниям моих радаров'."
)

# Выбираем современную и быструю модель (1.5 Flash отлично подходит для диалогов)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# --- [ НАСТРОЙКИ БОТА ] ---
MARTY_CHAT_TOKEN = os.getenv('MARTY_CHAT_TOKEN')
chat_bot = telebot.TeleBot(MARTY_CHAT_TOKEN, threaded=True)

# Словарь для хранения истории диалогов (памяти) для каждого пользователя/группы
active_chats = {}

def get_chat_session(chat_id):
    """Создает новую сессию с памятью или возвращает существующую"""
    if chat_id not in active_chats:
        active_chats[chat_id] = model.start_chat(history=[])
    
    # Очистка старой памяти, чтобы не перегружать сервер Render (храним последние 10 сообщений)
    if len(active_chats[chat_id].history) > 20: # 10 вопросов + 10 ответов
        active_chats[chat_id].history = active_chats[chat_id].history[-20:]
        
    return active_chats[chat_id]

# --- [ ОБРАБОТЧИК СООБЩЕНИЙ ] ---
@chat_bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_conversation(message):
    chat_id = message.chat.id
    text = message.text

    # ЛОГИКА ДЛЯ ГРУПП (Комментариев)
    if message.chat.type in ['group', 'supergroup']:
        bot_info = chat_bot.get_me()
        bot_username = f"@{bot_info.username}"
        
        # Проверяем, ответили ли боту напрямую или упомянули его по юзернейму
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id
        is_mentioned = bot_username in text

        if not (is_reply_to_bot or is_mentioned):
            return # Если просто общаются между собой — Марти молчит
        
        # Убираем юзернейм из текста, чтобы нейросеть читала только сам вопрос
        text = text.replace(bot_username, "").strip()

    if not text:
        return

    chat_bot.send_chat_action(chat_id, 'typing')
    
    try:
        # Достаем память именно этого чата и отправляем запрос в Gemini
        session = get_chat_session(chat_id)
        response = session.send_message(text)
        chat_bot.reply_to(message, response.text, parse_mode='Markdown')
    except Exception as e:
        chat_bot.reply_to(message, "📡 Ой, связь со спутником прервалась из-за метеоритного дождя! Повтори свой запрос.")
        print(f"[ОШИБКА GEMINI]: {e}")

# --- [ ЗАПУСК ] ---
def run_chat_bot():
    print("🤖 [СИСТЕМА] Бот-собеседник Марти выходит на связь...")
    chat_bot.polling(non_stop=True, interval=2, timeout=60)

