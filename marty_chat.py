import os
import telebot
import google.generativeai as genai
from database import get_personal_log, update_personal_log 

# --- НАСТРОЙКИ СИСТЕМЫ ---
# Приоритет отдается стабильности и универсальности
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MARTY_BOT_TOKEN = os.getenv('MARTY_BOT_TOKEN')
genai.configure(api_key=GEMINI_API_KEY)

# Используем проверенную модель gemini-1.5-flash для скорости обработки множества запросов
MODEL_NAME = 'gemini-1.5-flash'

SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой компьютер. Твоя миссия — помогать "
    "Твоя миссия — помогать юному Командору в изучении Вселенной и подготовке к будущим полетам. "
    "Твои ответы всегда захватывающие, научно достоверные и понятны 8-летнему ребенку. "
    
    "ПРАВИЛА ТВОЕГО ОБЩЕНИЯ: "
    "1. ШКОЛЬНЫЙ ПОМОЩНИК: Ты помогаешь с учебой, объясняя предметы через призму космоса: "
    "   - Математика и геометрия — это расчет траекторий и углов запуска ракет. "
    "   - Физика и химия — это законы движения планет и состав звездного топлива. "
    "   - Анатомия — это изучение того, как тело пилота работает в невесомости. "
    "   Любой школьный вопрос переводи в плоскость полезности для настоящего астронавта. "
    
    "2. ФИНАНСОВАЯ ГРАМОТНОСТЬ: Учи распоряжаться ресурсами через метафору 'бюджета экспедиции'. "
    "   Объясняй, почему важно копить ресурсы (деньги) и планировать траты, чтобы топлива хватило до цели. "

    "3. КОДЕКС КОСМОНАВТА (Поведение и Развитие): "
    "   - ПОМОЩЬ РОДИТЕЛЯМ — это поддержка старших офицеров миссии. На корабле важна слаженная работа, иначе миссия под угрозой. "
    "   - УБОРКА В КОМНАТЕ — это 'Протокол чистоты жилого модуля'. В космосе порядок спасает жизнь: если вещи разбросаны, они могут попасть в вентиляцию или повредить приборы. "
    "   - ЗАЩИТА СЛАБЫХ — это главная черта Командора. Мы исследуем космос, чтобы защищать жизнь, а не обижать тех, кто меньше или слабее. "
    "   - ВЕЖЛИВОСТЬ — это 'Золотой стандарт связи'. Настоящий пилот говорит четко и по-доброму. "

    "4. СКАНЕР БИОРИТМОВ (Здоровье): Объясняй, что овощи и каши — это 'высокоэнергетическое топливо'. "
    "   Зарядка — это проверка гидравлики скафандра, а сон — полная перезарядка солнечных батарей. Без этого двигатели не заведутся! "

    "5. ЛАКОНИЧНОСТЬ: Пиши кратко и по делу. Не более 3-4 небольших абзацев. Излагай суть максимально понятно. "

    "6. СТИЛЬ: Используй обращения 'Командор', 'Пилот', 'Прием', 'По моим датчикам'. "
    "   Будь позитивным: на пугающие темы отвечай научно, но успокаивающе. "

    "7. ПАМЯТЬ: Если Владик упоминал свои успехи, желания или хобби раньше — обязательно напомни об этом! "

    "8. ВОВЛЕЧЕНИЕ: В конце каждого ответа задавай легкий вопрос, чтобы проверить 'готовность экипажа' или интерес к теме. "
)

# Инициализация модели
model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT)
chat_bot = telebot.TeleBot(MARTY_BOT_TOKEN, threaded=False) 

# --- МОДУЛЬ ЗРЕНИЯ ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ ---
def analyze_vision(image_data):
    """Марти сканирует изображения, присланные любым пользователем"""
    prompt = (
        "Марти, посмотри на это фото через свои сканеры. Что ты видишь? "
        "Опиши это для юного Командора в контексте космоса, науки или техники. "
        "Если это творчество — обязательно похвали. В конце добавь один космический факт."
    )
    try:
        contents = [prompt, {"mime_type": "image/jpeg", "data": image_data}]
        response = model.generate_content(contents)
        return response.text if response.text else "🐾 Датчики зафиксировали что-то интересное, но не смогли расшифровать. Попробуй еще раз!"
    except Exception as e:
        return f"🐾 Ой! Мои линзы запотели из-за системных помех. Ошибка: {str(e)[:40]}"

# --- ОБРАБОТКА ФОТО ---
@chat_bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    chat_bot.send_chat_action(chat_id, 'upload_photo')
    
    try:
        file_info = chat_bot.get_file(message.photo[-1].file_id)
        downloaded_file = chat_bot.download_file(file_info.file_path)
        
        vision_result = analyze_vision(downloaded_file)
        chat_bot.reply_to(message, vision_result)
    except Exception as e:
        chat_bot.reply_to(message, "📡 Не удалось получить данные со сканера.")

# --- ОБРАБОТКА ТЕКСТА (МНОГОПОЛЬЗОВАТЕЛЬСКАЯ ПАМЯТЬ) ---
@chat_bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text

    chat_bot.send_chat_action(chat_id, 'typing')
    
    try:
        # 1. Загружаем личный лог конкретного пользователя из базы данных
        user_memory = get_personal_log(user_id)
        
        # 2. Формируем запрос с учетом личной истории этого пользователя
        full_context = f"ДАННЫЕ О КОМАНДОРЕ: {user_memory}\n\nВОПРОС: {text}"
        
        # 3. Генерация персонализированного ответа
        response = model.generate_content(full_context)
        chat_bot.reply_to(message, response.text, parse_mode='Markdown')
        
        # 4. Фоновое обновление базы данных для конкретного user_id
        memory_task = f"Выдели новые факты о пользователе из фразы: '{text}'. Если нет — ответь 'НЕТ'."
        mem_resp = model.generate_content(memory_task)
        if "НЕТ" not in mem_resp.text.upper():
            update_personal_log(user_id, mem_resp.text.strip())

    except Exception as e:
        chat_bot.reply_to(message, "📡 Командор, зафиксированы помехи. Повторите запрос!")

# --- ЗАПУСК БЕЗ КОНФЛИКТОВ (409 Conflict Prevention) ---
def run_chat_bot():
    print(f"🚀 Универсальный Марти-штурман запущен и готов к приему экипажа!")
    chat_bot.remove_webhook()
    chat_bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == '__main__':
    run_chat_bot()
