import os
import telebot
import google.generativeai as genai

# --- [ НАСТРОЙКИ НЕЙРОСЕТИ ] ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Инструкция, задающая характер и ограничения бота
SYSTEM_PROMPT = (
    "Ты — Марти, дружелюбный бортовой компьютер и космический гид Telegram-канала 'Дневник юного космонавта'. "
    "Твоя задача — увлекательно, но научно достоверно рассказывать про космос, планеты, звезды, МКС, экспедиции и астрономию. "
    "Твои ответы должны быть понятны 8-летним детям, используй сравнения из их жизни. "
    "Если тебя спрашивают о чем-то земном (игры, математика, рецепты, политика, школьные уроки), вежливо отвечай, что твои антенны "
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

# Проверка, чтобы сервер не падал, если вы забудете добавить токен в Render
if MARTY_CHAT_TOKEN is None:
    print("❌ [ОШИБКА] Токен MARTY_CHAT_TOKEN не найден в настройках Environment Variables!")
    chat_bot = None
else:
    chat_bot = telebot.TeleBot(MARTY_CHAT_TOKEN, threaded=True)

# Словарь для хранения истории диалогов (памяти) для каждого пользователя/группы
active_chats = {}

def get_chat_session(chat_id):
    """Создает новую сессию с памятью или возвращает существующую"""
    if chat_id not in active_chats:
        active_chats[chat_id] = model.start_chat(history=[])
    
    # Очистка старой памяти, чтобы не перегружать сервер (храним последние 10 сообщений)
    if len(active_chats[chat_id].history) > 20: # 10 вопросов + 10 ответов
        active_chats[chat_id].history = active_chats[chat_id].history[-20:]
        
    return active_chats[chat_id]

# --- [ ОБРАБОТЧИК СООБЩЕНИЙ ] ---
if chat_bot:
    @chat_bot.message_handler(func=lambda message: True, content_types=['text'])
    def handle_conversation(message):
        chat_id = message.chat.id
        text = message.text

        # ЛОГИКА ДЛЯ ГРУПП (Комментариев)
        if message.chat.type in ['group', 'supergroup']:
            bot_info = chat_bot.get_me()
            bot_username = f"@{bot_info.username}"
            
            text_lower = text.lower()
            
            # Проверяем, ответили ли боту (Reply), тегнули ли его, или назвали по имени
            is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id
            is_mentioned = bot_username in text
            is_called_by_name = "марти" in text_lower 

            # Если ни одно из условий не совпало — бот молчит
            if not (is_reply_to_bot or is_mentioned or is_called_by_name):
                return 
            
            # Очищаем текст от обращений, чтобы нейросети достался только сам вопрос
            text = text.replace(bot_username, "").replace("Марти", "").replace("марти", "").strip()
            
            # Убираем запятую в начале, если человек написал "Марти, расскажи..."
            if text.startswith(','):
                text = text[1:].strip()

        # Если после очистки имени текст оказался пустым (например, написали просто "Марти")
        if not text:
            chat_bot.reply_to(message, "На связи, Командор! Жду твоих вопросов о космосе. 🚀")
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
    if chat_bot:
        print("🤖 [СИСТЕМА] Бот-собеседник Марти выходит на связь...")
        chat_bot.polling(non_stop=True, interval=2, timeout=60)
    else:
        print("⏸️ [СИСТЕМА] Бот-собеседник отключен (не указан токен).")
