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
    if not os.path.exists(filename): return set()
    with open(filename, "r") as f:
        return set(line.strip() for line in f)

def save_id(filename, launch_id):
    with open(filename, "a") as f:
        f.write(f"{launch_id}\n")

# --- 🌐 ПЕРЕВОД И ОФОРМЛЕНИЕ ---
def translate_to_russian(text):
    try:
        if not text: return ""
        return GoogleTranslator(source='auto', target='ru').translate(text)
    except Exception: return text

def get_short_facts(text, icon):
    if not text or len(text) < 10:
        return f"{icon} Детали скоро появятся! 🛰️"
    sentences = [s.strip() for s in text.split('. ') if s.strip()]
    formatted_facts = []
    for fact in sentences[:3]:
        if ':' in fact:
            header, desc = fact.split(':', 1)
            formatted_facts.append(f"{icon} <b>{header}:</b>{desc}.")
        else:
            formatted_facts.append(f"{icon} {fact}.")
    return "\n\n".join(formatted_facts)

# --- 📡 РАБОТА С ТЕЛЕГРАМОМ ---
def send_to_telegram(text, photo_url=None):
    if photo_url:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': text, 'parse_mode': 'HTML'}
    else:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {'chat_id': CHANNEL_NAME, 'text': text, 'parse_mode': 'HTML'}
    requests.post(api_url, data=payload)

# --- 🚀 ОСНОВНОЙ ЦИКЛ МАРТИ ---
if __name__ == '__main__':
    print("--- 🏁 Марти выходит на связь ---")
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=1"
    
    try:
        response = requests.get(url).json()
        launch = response['results'][0] if response.get('results') else None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        launch = None

    if launch:
        launch_id = launch['id']
        rocket_data = launch['rocket']['configuration']
        rocket_name = rocket_data['name']
        pad_name = launch['pad']['name']
        location_name = launch['pad']['location']['name']
        launch_time = datetime.fromisoformat(launch['net'].replace('Z', '+00:00'))
        
        # --- 🕵️‍♂️ ЛОГИКА ИЩЕЙКИ (Поиск лучшей ссылки) ---
        potential_urls = []
        for v in launch.get('vidURLs', []): potential_urls.append(v.get('url'))
        for i in launch.get('infoURLs', []): potential_urls.append(i.get('url'))

        best_video = None
        for url in potential_urls:
            if url and ("youtube" in url or "youtu.be" in url):
                best_video = url
                break
        if not best_video and potential_urls:
            best_video = potential_urls[0]

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
            "🍭 <b>ПЛАНЕТА-ЗЕФИРКА:</b> Есть планета, которые плавали бы в ванне!",
            "🧊 <b>ЛЕДЯНЫЕ ЛУНЫ:</b> У Юпитера есть луна Европа с океаном под льдом!",
            "🧲 <b>МАГНИТНАЯ ЗАЩИТА:</b> Земля — это магнит, защищающий нас от лучей!",
            "⏳ <b>РАЗНОЕ ВРЕМЯ:</b> В космосе время идет иначе, чем на Земле!",
            "📡 <b>ПЕРВЫЙ СИГНАЛ:</b> Первый спутник просто передавал «Бип-бип»!",
            "👨‍🚀 <b>ЮРИЙ ГАГАРИН:</b> Его полет длился всего 108 минут!",
            "⛽ <b>ЗАПРАВКА:</b> Корабли могут заправляться прямо на орбите!",
            "🎂 <b>ДЕНЬ РОЖДЕНИЯ:</b> Марсоход Curiosity сам спел себе песню на Марсе!"
        ]

        # --- 📦 БЛОК 1: ПОЛНЫЙ АНОНС ---
        sent_main = load_ids(DB_FILE)
        if launch_id not in sent_main:
            mission_name = launch['mission']['name'] if launch['mission'] else "Секретная миссия"
            raw_mission_desc = launch['mission']['description'] if launch['mission'] else ""
            short_mission = get_short_facts(translate_to_russian(raw_mission_desc), "🛰️")
            
            raw_rocket_desc = rocket_data.get('description', "")
            short_rocket = get_short_facts(translate_to_russian(raw_rocket_desc), "🚀")
            
            video_btn = f"\n\n📺 <b>ГДЕ СМОТРЕТЬ:</b>\n• <a href='{best_video}'>Смотреть трансляцию 📺</a>" if best_video else ""
            
            report = (f"🚀 <b>СКОРО В КОСМОС: {rocket_name.upper()}</b>\n"
                      f"🎯 <b>Миссия:</b> {mission_name}\n"
                      f"⏰ <b>Старт:</b> {launch_time.strftime('%d.%m %H:%M')} UTC\n"
                      f"📍 <b>Место:</b> {pad_name}, {location_name}\n\n"
                      f"📋 <b>О МИССИИ:</b>\n{short_mission}\n\n"
                      f"🚀 <b>ТЕХНИКА:</b>\n{short_rocket}{video_btn}\n\n"
                      f"--------------------------\n"
                      f"🎒 <b>МАРТИ РАССКАЗЫВАЕТ:</b>\n{random.choice(secrets)}\n"
                      f"--------------------------\n\n"
                      f"🌌 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")
            
            send_to_telegram(report, launch.get('image'))
            save_id(DB_FILE, launch_id)

        # --- 🔔 БЛОК 2: НАПОМИНАНИЕ (5 МИНУТ) ---
        time_to_start = (launch_time - datetime.now(timezone.utc)).total_seconds()
        if 0 < time_to_start <= 300:
            sent_reminders = load_ids(REMINDERS_FILE)
            if launch_id not in sent_reminders:
                link_text = f"\n\n📺 <a href='{best_video}'>ЗАПУСТИТЬ ТРАНСЛЯЦИЮ</a>" if best_video else ""
                reminder = (f"🎒 <b>МАРТИ: 5 МИНУТ ДО СТАРТА!</b>\n\n"
                           f"Ракета <b>{rocket_name}</b> уже на старте! Готовимся к отрыву! 🚀✨{link_text}")
                send_to_telegram(reminder)
                save_id(REMINDERS_FILE, launch_id)
