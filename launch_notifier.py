import requests
import os
import random
from datetime import datetime, timezone
from deep_translator import GoogleTranslator

# --- ⚙️ НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  # Твой токен из переменных окружения
CHANNEL_NAME = '@vladislav_space'             # Ссылка на твой канал
DB_FILE = "sent_launches.txt"                # База данных отправленных анонсов
REMINDERS_FILE = "sent_reminders.txt"        # База данных отправленных напоминаний

# --- 🧠 ФУНКЦИИ ПАМЯТИ ---
def load_ids(filename):
    """Загружает ID запусков, о которых мы уже рассказали, чтобы не спамить 📄"""
    if not os.path.exists(filename):
        return set()
    with open(filename, "r") as f:
        return set(line.strip() for line in f)

def save_id(filename, launch_id):
    """Записывает ID запуска в файл, чтобы помнить о нем 💾"""
    with open(filename, "a") as f:
        f.write(f"{launch_id}\n")

# --- 🌐 ПЕРЕВОД И ОФОРМЛЕНИЕ ТЕКСТА ---
def translate_to_russian(text):
    """Переводит английский текст от NASA на русский 🇷🇺"""
    try:
        if not text: return ""
        return GoogleTranslator(source='auto', target='ru').translate(text)
    except Exception:
        return text

def get_short_facts(text, icon):
    """
    Делает текст красивым: берет 3 факта, ищет двоеточие,
    делает заголовок жирным и добавляет нужную иконку 🎨
    """
    if not text or len(text) < 10:
        return f"{icon} Детали скоро появятся! 🛰️"
    
    # Делим текст на предложения
    sentences = [s.strip() for s in text.split('. ') if s.strip()]
    top_facts = sentences[:3] # Берем первые три
    
    formatted_facts = []
    for fact in top_facts:
        if ':' in fact:
            # Если есть двоеточие, разделяем на заголовок и описание
            header, description = fact.split(':', 1)
            formatted_facts.append(f"{icon} <b>{header}:</b>{description}.")
        else:
            # Если двоеточия нет, просто ставим иконку
            formatted_facts.append(f"{icon} {fact}.")
            
    return "\n\n".join(formatted_facts)

# --- 📡 РАБОТА С ДАННЫМИ ---
def check_launches():
    """Стучится в API The Space Devs за свежими запусками 🛰️"""
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=1"
    try:
        response = requests.get(url).json()
        if not response.get('results'):
            return None
        return response['results'][0]
    except Exception as e:
        print(f"❌ Ошибка связи с космосом: {e}")
        return None

def send_to_telegram(text, photo_url=None):
    """Отправляет пост в Telegram: с картинкой или без 🚀"""
    if photo_url:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': text, 'parse_mode': 'HTML'}
    else:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {'chat_id': CHANNEL_NAME, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': False}
    requests.post(api_url, data=payload)

# --- 🛰️ ЗАПУСК БОТА ---
if __name__ == '__main__':
    print("--- 🏁 Марти начинает проверку горизонтов ---")
    launch = check_launches()
    
    if launch:
        launch_id = launch['id']
        # Собираем данные о ракете и месте старта
        rocket_data = launch['rocket']['configuration']
        rocket_name = rocket_data['name']
        pad_name = launch['pad']['name']
        location_name = launch['pad']['location']['name']
        
        image_url = launch.get('image')
        video_links = launch.get('vidURLs', [])
        
        # Разбираемся со временем (UTC)
        launch_time = datetime.fromisoformat(launch['net'].replace('Z', '+00:00'))
        
        # --- 📦 БЛОК 1: ПОЛНЫЙ АНОНС ---
        sent_main = load_ids(DB_FILE)
        if launch_id not in sent_main:
            mission_name = launch['mission']['name'] if launch['mission'] else "Секретная миссия"
            time_str = launch_time.strftime('%d.%m в %H:%M')

            # Готовим описания (Миссия + Ракета)
            raw_mission_desc = launch['mission']['description'] if launch['mission'] else ""
            short_mission = get_short_facts(translate_to_russian(raw_mission_desc), "🛰️")

            raw_rocket_desc = rocket_data.get('description', "")
            short_rocket = get_short_facts(translate_to_russian(raw_rocket_desc), "🚀")
            
            # 🎒 ЗОЛОТОЙ ЗАПАС ЗНАНИЙ МАРТИ (50 ФАКТОВ)
            secrets = [
                "🎒 <b>ПРИНЦИП РЮКЗАКА:</b> Ракета сбрасывает пустые баки, чтобы лететь налегке!",
                "🌊 <b>ОГРОМНЫЙ ДУШ:</b> Воду льют под ракету, чтобы звук не сломал её!",
                "⚪ <b>ПОЧЕМУ БЕЛЫЙ?</b> Этот цвет отражает солнце, чтобы топливо не перегрелось!",
                "🔥 <b>ОГНЕННЫЙ ХВОСТ:</b> Дым из ракеты — это водяной пар и сгоревшее топливо!",
                "🌑 <b>СЛЕДЫ НА ЛУНЕ:</b> Они останутся там навсегда, ведь там нет ветра!",
                "🦒 <b>РОСТ КОСМОНАВТА:</b> В космосе человек становится выше на пару сантиметров!",
                "🍕 <b>КОСМИЧЕСКАЯ ЕДА:</b> Раньше ели из тюбиков, а теперь можно даже пиццу!",
                "🪐 <b>КОЛЬЦА САТУРНА:</b> Они состоят из миллиардов кусочков льда и камней!",
                "🛰️ <b>ПЕРВЫЙ СПУТНИК:</b> Он был размером с баскетбольный мяч!",
                "📸 <b>СЕЛФИ:</b> Первое селфи в открытом космосе сделали в 1966 году!",
                "🦷 <b>СЪЕДОБНАЯ ПАСТА:</b> Зубную пасту в космосе приходится глотать!",
                "🧂 <b>ЖИДКАЯ СОЛЬ:</b> Соль в космосе жидкая, чтобы не разлетелась!",
                "🥛 <b>ЛЕЖАЧАЯ ВОДА:</b> Вода в космосе собирается в шарики!",
                "🧺 <b>БЕЗ СТИРКИ:</b> Одежду в космосе не стирают — её просто выбрасывают!",
                "👃 <b>ЗАПАХ КОСМОСА:</b> Космос пахнет жареным стейком или металлом!",
                "☀️ <b>16 РАССВЕТОВ:</b> Космонавты видят рассвет 16 раз в сутки!",
                "🥗 <b>КОСМИЧЕСКИЙ ОГОРОД:</b> На МКС выращивают салат в спецлампах!",
                "💇 <b>СТРИЖКА-ПЫЛЕСОС:</b> При стрижке используют пылесос!",
                "💎 <b>АЛМАЗНАЯ ПЛАНЕТА:</b> Есть планета, состоящая из алмаза!",
                "🌋 <b>СУПЕР-ВУЛКАН:</b> На Марсе есть вулкан Олимп, он в 3 раза выше Эвереста!",
                "🌡️ <b>ЖАРКАЯ ВЕНЕРА:</b> Там можно расплавить свинец за секунду!",
                "🔴 <b>РЖАВЫЙ МАРС:</b> Марс красный, потому что его почва заржавела!",
                "🌀 <b>БОЛЬШОЕ ПЯТНО:</b> На Юпитере шторм идет уже 300 лет!",
                "🌌 <b>МЛЕЧНЫЙ ПУТЬ:</b> Наша галактика похожа на карусель!",
                "🐢 <b>ЧЕРЕПАХИ-ГЕРОИ:</b> Первыми облетели Луну две черепахи!",
                "🐕 <b>ЛАЙКА:</b> Собака Лайка была самым первым животным в космосе!",
                "🌠 <b>ПАДАЮЩИЕ ЗВЕЗДЫ:</b> Это маленькие камешки, сгорающие в воздухе!",
                "🌒 <b>ОБРАТНАЯ СТОРОНА:</b> Мы никогда не видим одну сторону Луны!",
                "👣 <b>ПРЫЖКИ:</b> На Луне ты мог бы прыгнуть в 6 раз выше!",
                "🧤 <b>СКОВАННЫЕ РУКИ:</b> Перчатки скафандра очень трудно сгибать!",
                "🔌 <b>СОЛНЕЧНЫЕ КРЫЛЬЯ:</b> У МКС огромные панели для тока!",
                "🧱 <b>КИРПИЧИ ИЗ ЛУНЫ:</b> Дома на Луне хотят строить из лунной пыли!",
                "🧨 <b>ПИРОБОЛТЫ:</b> Части ракеты отцепляются маленькими взрывами!",
                "🛡️ <b>ТЕПЛОВОЙ ЩИТ:</b> Дно корабля защищает его от жара в 1500 градусов!",
                "🛰️ <b>КОСМИЧЕСКИЙ МУСОР:</b> Вокруг Земли летают тысячи обломков ракет!",
                "🎈 <b>ВАКУУМ:</b> В космосе нет воздуха, нельзя дышать без шлема!",
                "🤖 <b>РОБОТЫ-ПОМОЩНИКИ:</b> На МКС живут роботы с именами!",
                "🔭 <b>ЗОЛОТОЕ ЗЕРКАЛО:</b> У телескопа Уэбб зеркало покрыто золотом!",
                "🌍 <b>СКОРОСТЬ ПУЛИ:</b> Чтобы выйти в космос, нужно лететь в 10 раз быстрее пули!",
                "💤 <b>СОН В СТАКАНЕ:</b> Космонавты спят в мешках у стены!",
                "🚿 <b>ВМЕСТО ДУША:</b> В космосе моются влажными полотенцами!",
                "🤐 <b>ТИШИНА:</b> В космосе абсолютная тишина!",
                "🍭 <b>ПЛАНЕТА-ЗЕФИРКА:</b> Есть планеты, которые плавали бы в ванне!",
                "🧊 <b>ЛЕДЯНЫЕ ЛУНЫ:</b> У Юпитера есть луна Европа с океаном под льдом!",
                "🧲 <b>МАГНИТНАЯ ЗАЩИТА:</b> Земля — это магнит, защищающий нас от лучей!",
                "⏳ <b>РАЗНОЕ ВРЕМЯ:</b> В космосе время идет иначе, чем на Земле!",
                "📡 <b>ПЕРВЫЙ СИГНАЛ:</b> Первый спутник просто передавал «Бип-бип»!",
                "👨‍🚀 <b>ЮРИЙ ГАГАРИН:</b> Его полет длился всего 108 минут!",
                "⛽ <b>ЗАПРАВКА:</b> Корабли могут заправляться прямо на орбите!",
                "🎂 <b>ДЕНЬ РОЖДЕНИЯ:</b> Марсоход Curiosity сам спел себе песню на Марсе!"
            ]
            
            # Ссылка на трансляцию
            video_section = ""
            if video_links:
                video_section = "\n\n📺 <b>ГДЕ СМОТРЕТЬ:</b>"
                for link in video_links:
                    v_url = link['url']
                    source = "YouTube 📺" if "youtube" in v_url or "youtu.be" in v_url else "Официальный сайт 🌐"
                    video_section += f"\n• <a href='{v_url}'>{source}</a>"

            # СОБИРАЕМ ИТОГОВЫЙ ПОСТ
            report = (f"🚀 <b>СКОРО В КОСМОС: {rocket_name.upper()}</b>\n"
                      f"🎯 <b>Миссия:</b> {mission_name}\n"
                      f"⏰ <b>Время старта:</b> {time_str} (UTC)\n"
                      f"📍 <b>Место:</b> {pad_name}, {location_name}\n\n"
                      f"📋 <b>О МИССИИ:</b>\n{short_mission}\n\n"
                      f"🚀 <b>ТЕХНИКА:</b>\n{short_rocket}"
                      f"{video_section}\n\n"
                      f"--------------------------\n"
                      f"🎒 <b>МАРТИ РАССКАЗЫВАЕТ:</b>\n{random.choice(secrets)}\n"
                      f"--------------------------\n\n"
                      f"🌌 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")
            
            send_to_telegram(report, image_url)
            save_id(DB_FILE, launch_id)

        # --- 🔔 БЛОК 2: НАПОМИНАНИЕ (5 МИНУТ) ---
        now = datetime.now(timezone.utc)
        time_diff = launch_time - now
        if 0 < time_diff.total_seconds() <= 300:
            sent_reminders = load_ids(REMINDERS_FILE)
            if launch_id not in sent_reminders:
                reminder_text = (
                    f"🎒 <b>МАРТИ: ВСЕМ ПРИГОТОВИТЬСЯ!</b>\n\n"
                    f"До старта <b>{rocket_name}</b> осталось всего <b>5 минут</b>! ⏱️\n"
                    f"Проверьте системы и не пропустите момент отрыва! 🚀✨"
                )
                send_to_telegram(reminder_text)
                save_id(REMINDERS_FILE, launch_id)
    
    print("--- 🏁 Проверка завершена ---")
