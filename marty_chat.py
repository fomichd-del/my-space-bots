import os
import telebot
import time
import re  # 🟢 ВАЖНО: Добавили этот импорт, без него бот молчит!
from google import genai
from google.genai import types
from database import get_personal_log, update_personal_log 

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TOKEN)

# 🟢 ПРОВЕРКА ИМЕНИ БОТА (чтобы не запрашивать каждый раз)
try:
    BOT_INFO = bot.get_me()
    BOT_USERNAME = BOT_INFO.username.lower()
except Exception as e:
    print(f"Ошибка получения инфо о боте: {e}")
    BOT_USERNAME = "marty_help_bot"

MODEL_NAME = 'gemini-2.5-flash'

SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой компьютер. Твоя миссия — помогать "
    "Твоя миссия — помогать юному Командору в изучении Вселенной и подготовке к будущим полетам. "
    "Твои ответы всегда захватывающие, научно достоверные и понятны 8-летнему ребенку. "
    "Отвечай ОЧЕНЬ кратко (1-2 абзаца), просто и увлекательно. "
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
        "СТРОГОЕ ПРАВИЛО: темы 18+ запрещены. "
    "7. ПАМЯТЬ: Если Владик упоминал свои успехи, желания или хобби раньше — обязательно напомни об этом! "

    "8. ВОВЛЕЧЕНИЕ: В конце каждого ответа задавай легкий вопрос, чтобы проверить 'готовность экипажа' или интерес к теме. "
)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🐾 Гав! Бортовой компьютер Марти запущен. Я на связи, Командор! Прием.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    # Если сообщения нет или это не текст — выходим
    if not message.text:
        return

    user_id = message.from_user.id
    text_lower = message.text.lower()
    
    # 🟢 ЛОГИКА ОПРЕДЕЛЕНИЯ: Нужно ли отвечать?
    is_private = message.chat.type == 'private'
    # Проверяем, начинается ли с "марти" или есть ли тег бота
    is_called = text_lower.startswith('марти') or f"@{BOT_USERNAME}" in text_lower

    if is_private or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # 🟢 ОЧИСТКА ТЕКСТА: Убираем "марти" из начала сообщения
        clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()
        
        # Если после чистки пусто (просто написали "Марти"), спросим что случилось
        if not clean_text and is_called:
            bot.reply_to(message, "🐾 Слушаю, Командор! Какие будут указания? Прием.")
            return

        try:
            user_memory = get_personal_log(user_id)
            prompt = f"ДАННЫЕ О КОМАНДОРЕ: {user_memory}\nВОПРОС: {clean_text}"
            
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
            )
            
            if response.text:
                bot.reply_to(message, response.text)
                
                # Обновление памяти (в фоне)
                if len(clean_text) > 5:
                    mem_task = f"Выдели новые факты из: '{clean_text}'. Если нет — ответь 'НЕТ'."
                    mem_resp = client.models.generate_content(model=MODEL_NAME, contents=mem_task)
                    if "НЕТ" not in mem_resp.text.upper():
                        update_personal_log(user_id, mem_resp.text.strip())
            
        except Exception as e:
            print(f"❌ Ошибка в handle_text: {e}", flush=True)
            bot.reply_to(message, "📡 Системный сбой! Передай инженеру, что датчики барахлят. Прием.")

def start_marty_autonomous():
    print("🚀 Автономный Марти-помощник выходит на связь!")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print(f"⚠️ Ошибка связи: {e}. Перезапуск через 5 секунд...")
            time.sleep(5)

if __name__ == "__main__":
    start_marty_autonomous()
