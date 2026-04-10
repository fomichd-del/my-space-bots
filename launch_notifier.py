import requests
import os
import random
import json
from datetime import datetime, timezone
from deep_translator import GoogleTranslator

# --- ⚙️ НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'
DB_FILE = "sent_launches.txt"
REMINDERS_FILE = "sent_reminders.txt"

translator = GoogleTranslator(source='auto', target='ru')

# 🎒 ПОЛНЫЙ ЗОЛОТОЙ ЗАПАС ЗНАНИЙ МАРТИ (50 ФАКТОВ)
SECRETS = [
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

def load_ids(filename):
    if not os.path.exists(filename): return set()
    with open(filename, "r", encoding='utf-8') as f:
        return set(line.strip() for line in f)

def save_id(filename, launch_id):
    with open(filename, "a", encoding='utf-8') as f:
        f.write(f"{launch_id}\n")

def get_short_facts(text, icon):
    if not text: return f"{icon} Детали появятся позже."
    try:
        ru_text = translator.translate(text)
        sentences = [s.strip() for s in ru_text.split('. ') if s.strip()]
        return "\n".join([f"{icon} {s}." for s in sentences[:3]])
    except: return f"{icon} {text[:100]}..."

def send_to_telegram(text, photo_url=None):
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    if photo_url:
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': text, 'parse_mode': 'HTML'}
        r = requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        payload = {'chat_id': CHANNEL_NAME, 'text': text, 'parse_mode': 'HTML'}
        r = requests.post(f"{base_url}/sendMessage", data=payload)
    print(f"📡 Ответ Telegram: {r.status_code}")

def check_launches():
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=1"
    print(f"📡 Запрашиваю данные о запусках...")
    try:
        response = requests.get(url, timeout=25)
        res = response.json()
        launch = res['results'][0] if res.get('results') else None
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return

    if launch:
        launch_id = launch['id']
        rocket_name = launch['rocket']['configuration']['name']
        launch_time = datetime.fromisoformat(launch['net'].replace('Z', '+00:00'))
        print(f"🔎 Вижу запуск: {rocket_name} (ID: {launch_id})")

        # 1. ОСНОВНОЙ АНОНС
        sent_main = load_ids(DB_FILE)
        if launch_id not in sent_main:
            print("🆕 Это новый запуск. Отправляю анонс...")
            mission_name = launch['mission']['name'] if launch['mission'] else "Секретная"
            short_mission = get_short_facts(launch['mission']['description'] if launch['mission'] else "", "🛰️")
            short_rocket = get_short_facts(launch['rocket']['configuration'].get('description', ""), "🚀")
            
            best_video = None
            vid_urls = launch.get('vidURLs', [])
            if vid_urls: best_video = vid_urls[0].get('url')
            video_btn = f"\n\n📺 <b>ТРАНСЛЯЦИЯ:</b>\n• <a href='{best_video}'>Смотреть запуск</a>" if best_video else ""
            
            report = (f"🚀 <b>СКОРО В КОСМОС: {rocket_name.upper()}</b>\n"
                      f"─────────────────────\n"
                      f"🎯 <b>Миссия:</b> {mission_name}\n"
                      f"⏰ <b>Старт:</b> {launch_time.strftime('%d.%m %H:%M')} UTC\n"
                      f"📍 <b>Место:</b> {launch['pad']['location']['name']}\n\n"
                      f"<b>О МИССИИ:</b>\n{short_mission}\n\n"
                      f"<b>ТЕХНИКА:</b>\n{short_rocket}{video_btn}\n\n"
                      f"🎒 <b>МАРТИ РАССКАЗЫВАЕТ:</b>\n{random.choice(SECRETS)}\n\n"
                      f"🌌 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")
            
            send_to_telegram(report, launch.get('image'))
            save_id(DB_FILE, launch_id)
        else:
            print("✋ Анонс этого запуска уже был в канале.")

        # 2. НАПОМИНАНИЕ (10 минут до старта)
        time_to_start = (launch_time - datetime.now(timezone.utc)).total_seconds()
        print(f"⏳ До старта: {round(time_to_start/60, 1)} мин.")
        
        if 0 < time_to_start <= 600:
            sent_reminders = load_ids(REMINDERS_FILE)
            if launch_id not in sent_reminders:
                print("🔔 Отправляю напоминание (5 минут до старта)...")
                reminder = (f"🎒 <b>МАРТИ: ГОТОВНОСТЬ 5 МИНУТ!</b>\n"
                           f"─────────────────────\n\n"
                           f"Ракета <b>{rocket_name}</b> уже на старте! Готовимся к отрыву! 🚀✨\n\n"
                           f"🌌 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")
                send_to_telegram(reminder)
                save_id(REMINDERS_FILE, launch_id)
            else:
                print("✋ Напоминание уже было.")
    else:
        print("📭 Ближайших запусков не найдено.")

if __name__ == '__main__':
    check_launches()
