import requests
import os
import random
from datetime import datetime, timezone
from deep_translator import GoogleTranslator

# --- ⚙️ НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'
DB_FILE = "sent_launches.txt"          
REMINDERS_FILE = "sent_reminders.txt"  

# --- 🧠 ФУНКЦИИ ПАМЯТИ ---
def load_ids(filename):
    if not os.path.exists(filename):
        return set()
    with open(filename, "r") as f:
        return set(line.strip() for line in f)

def save_id(filename, launch_id):
    with open(filename, "a") as f:
        f.write(f"{launch_id}\n")

# --- 🌐 ПЕРЕВОД И ДАННЫЕ ---
def translate_to_russian(text):
    try:
        if not text: return "Детали миссии скоро появятся! 🛰️"
        return GoogleTranslator(source='auto', target='ru').translate(text)
    except Exception:
        return text

def check_launches():
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=1"
    try:
        response = requests.get(url).json()
        if not response.get('results'):
            return None
        return response['results'][0]
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return None

def send_to_telegram(text, photo_url=None):
    if photo_url:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': text, 'parse_mode': 'HTML'}
    else:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {'chat_id': CHANNEL_NAME, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': False}
    requests.post(api_url, data=payload)

# --- 🚀 ОСНОВНОЙ ЦИКЛ ---
if __name__ == '__main__':
    print("--- 🏁 Марти на связи ---")
    launch = check_launches()
    
    if launch:
        launch_id = launch['id']
        rocket = launch['rocket']['configuration']['name']
        image_url = launch.get('image')
        video_links = launch.get('vidURLs', [])
        
        # Расчет времени
        launch_time = datetime.fromisoformat(launch['net'].replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        time_diff = launch_time - now
        seconds_to_launch = time_diff.total_seconds()

        # --- 📦 БЛОК 1: БОЛЬШОЙ АНОНС ---
        sent_main = load_ids(DB_FILE)
        if launch_id not in sent_main:
            mission_name = launch['mission']['name'] if launch['mission'] else "Космическая миссия"
            description = translate_to_russian(launch['mission']['description'] if launch['mission'] else "")
            
            # Список секретов
            secrets = [
                "🎒 <b>ПРИНЦИП РЮКЗАКА:</b> Ракета сбрасывает пустые баки, чтобы лететь налегке!",
                "🌊 <b>ОГРОМНЫЙ ДУШ:</b> Воду льют под ракету, чтобы звук не сломал её!",
                "⚪ <b>ПОЧЕМУ БЕЛЫЙ?</b> Этот цвет отражает солнце, чтобы топливо не грелось!",
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
            
            # Собираем ссылки для анонса
            video_section = ""
            if video_links:
                video_section = "\n\n📺 <b>ГДЕ СМОТРЕТЬ:</b>"
                for link in video_links:
                    url = link['url']
                    if "youtube.com" in url or "youtu.be" in url: source = "YouTube 📺"
                    elif "x.com" in url or "twitter.com" in url: source = "Сеть X (Twitter) 🐦"
                    else: source = "Официальный сайт 🌐"
                    video_section += f"\n• <a href='{url}'>{source}</a>"

            report = (f"🚀 <b>СКОРО В КОСМОС: {rocket.upper()}</b>\n"
                      f"🎯 <b>Миссия:</b> {mission_name}\n\n"
                      f"📋 <b>Описание:</b> {description}"
                      f"{video_section}\n\n"
                      f"--------------------------\n"
                      f"🎒 <b>МАРТИ РАССКАЗЫВАЕТ:</b>\n{random.choice(secrets)}\n"
                      f"--------------------------\n\n"
                      f"🌌 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")
            
            send_to_telegram(report, image_url)
            save_id(DB_FILE, launch_id)

        # --- 🔔 БЛОК 2: УМНЫЙ ТАЙМЕР (5 МИНУТ) ---
        if 0 < seconds_to_launch <= 300:
            sent_reminders = load_ids(REMINDERS_FILE)
            if launch_id not in sent_reminders:
                # Берем только одну ссылку для краткости
                main_link = ""
                if video_links:
                    url = video_links[0]['url']
                    main_link = f"\n\n📺 <a href='{url}'>Смотреть запуск</a>"

                reminder_text = (
                    f"🎒 <b>МАРТИ: ВСЕМ ПРИГОТОВИТЬСЯ!</b>\n\n"
                    f"До старта <b>{rocket}</b> осталось всего <b>5 минут</b>! ⏱️\n"
                    f"Проверьте системы и не пропустите момент отрыва! 🚀✨"
                    f"{main_link}"
                )
                
                send_to_telegram(reminder_text)
                save_id(REMINDERS_FILE, launch_id)
    
    print("--- 🏁 Проверка завершена ---")
