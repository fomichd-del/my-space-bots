import requests
import os
import random
from datetime import datetime, timezone
from deep_translator import GoogleTranslator

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'
DB_FILE = "sent_launches.txt"

def load_sent_ids():
    """Загружаем список уже отправленных ID 🧠"""
    if not os.path.exists(DB_FILE):
        return set()
    with open(DB_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_sent_id(launch_id):
    """Сохраняем новый ID в файл памяти 💾"""
    with open(DB_FILE, "a") as f:
        f.write(f"{launch_id}\n")

def translate_to_russian(text):
    """Переводим описание на русский язык 🌐"""
    try:
        return GoogleTranslator(source='auto', target='ru').translate(text)
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return text

def check_launches():
    """Проверяем API и собираем данные о запуске 🛰️"""
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=1"
    try:
        response = requests.get(url).json()
        if not response.get('results'):
            return None, None, None, None
        launch = response['results'][0]
    except Exception as e:
        print(f"Ошибка при запросе к API: {e}")
        return None, None, None, None

    launch_id = launch['id']
    rocket = launch['rocket']['configuration']['name']
    image_url = launch.get('image') 
    
    # Ищем ссылки на видео 📺
    video_links = launch.get('vidURLs', [])
    video_url = video_links[0]['url'] if video_links else None
    
    mission_name = launch['mission']['name'] if launch['mission'] else "Интересная миссия"
    raw_description = launch['mission']['description'] if launch['mission'] else "Детали появятся позже."
    description = translate_to_russian(raw_description)
    
    # Время до старта ⏱️
    launch_time_str = launch['net']
    launch_time = datetime.fromisoformat(launch_time_str.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    time_diff = launch_time - now
    
    if time_diff.total_seconds() > 0:
        hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        countdown = f"{hours}ч {minutes}м"
    else:
        countdown = "Запуск уже начался!"

    # Секреты Марти 🎒
    secrets_list = [
        "🎒 <b>ПРИНЦИП РЮКЗАКА:</b> Ракета сбрасывает пустые баки, чтобы лететь налегке! 🚀",
        "🌊 <b>ОГРОМНЫЙ ДУШ:</b> Воду льют под ракету, чтобы звук двигателей её не сломал! 🔊",
        "⚪ <b>ПОЧЕМУ БЕЛЫЙ?</b> Этот цвет отражает солнце, чтобы топливо не перегрелось! ☀️",
        "🔥 <b>ОГНЕННЫЙ ХВОСТ:</b> Дым из ракеты — это на самом деле водяной пар и сгоревшее топливо! 💨",
        "🌑 <b>СЛЕДЫ НА ЛУНЕ:</b> Следы Армстронга останутся там навсегда, ведь там нет ветра! 👣",
        "🦒 <b>РОСТ КОСМОНАВТА:</b> В космосе человек становится выше на пару сантиметров! 📏",
        "🍕 <b>КОСМИЧЕСКАЯ ЕДА:</b> Раньше ели из тюбиков, а теперь можно даже пиццу! 🍕",
        "🪐 <b>КОЛЬЦА САТУРНА:</b> Они состоят из миллиардов кусочков льда и камней! 🧊",
        "🛰️ <b>ПЕРВЫЙ СПУТНИК:</b> Он был размером с баскетбольный мяч и просто пищал! 🏀",
        "📸 <b>СЕЛФИ:</b> Первое селфи в открытом космосе сделал Базз Олдрин в 1966 году! 🤳",
        "🦷 <b>СЪЕДОБНАЯ ПАСТА:</b> Зубную пасту в космосе приходится глотать! 🪥",
        "🧂 <b>ЖИДКАЯ СОЛЬ:</b> Соль в космосе жидкая, иначе крупинки разлетятся везде! 💧",
        "🥛 <b>ЛЕЖАЧАЯ ВОДА:</b> Вода в космосе собирается в шарики, их можно ловить ртом! 🫧",
        "🧺 <b>БЕЗ СТИРКИ:</b> Одежду в космосе не стирают — грязную просто выбрасывают! 👕",
        "👃 <b>ЗАПАХ КОСМОСА:</b> Космос пахнет жареным стейком или жженым металлом! 🥩",
        "☀️ <b>16 РАССВЕТОВ:</b> Космонавты видят рассвет и закат 16 раз в сутки! 🌅",
        "🥗 <b>КОСМИЧЕСКИЙ ОГОРОД:</b> На станции выращивают салат в специальных лампах! 🥬",
        "💇 <b>СТРИЖКА-ПЫЛЕСОС:</b> При стрижке используют пылесос, чтобы волосы не улетели! 💇‍♂️",
        "💎 <b>АЛМАЗНАЯ ПЛАНЕТА:</b> Есть планета, которая, возможно, состоит из алмаза! 💎",
        "🌋 <b>СУПЕР-ВУЛКАН:</b> На Марсе есть вулкан Олимп, он в три раза выше Эвереста! 🏔️",
        "🌡️ <b>ЖАРКАЯ ВЕНЕРА:</b> Там так жарко, что можно расплавить свинец за секунду! 🥵",
        "🔴 <b>РЖАВЫЙ МАРС:</b> Марс красный, потому что его почва покрыта ржавчиной! 🧱",
        "🌀 <b>БОЛЬШОЕ ПЯТНО:</b> На Юпитере есть шторм, который идет уже 300 лет! 🌀",
        "🌌 <b>МЛЕЧНЫЙ ПУТЬ:</b> Наша галактика похожа на светящуюся карусель! 🎠",
        "🐢 <b>ЧЕРЕПАХИ-ГЕРОИ:</b> Первыми облетели Луну две обычные черепахи! 🐢",
        "🐕 <b>ЛАЙКА:</b> Собака Лайка была самым первым животным в космосе! 🐶",
        "🌠 <b>ПАДАЮЩИЕ ЗВЕЗДЫ:</b> Это просто маленькие камешки, сгорающие в воздухе! ✨",
        "🌒 <b>ОБРАТНАЯ СТОРОНА:</b> Мы никогда не видим одну сторону Луны с Земли! 🌒",
        "👣 <b>ПРЫЖКИ:</b> На Луне ты мог бы прыгнуть в 6 раз выше, чем дома! 🦘",
        "🧤 <b>СКОВАННЫЕ РУКИ:</b> Перчатки скафандра так сильно раздуваются, что ими трудно шевелить! 🧤",
        "🔌 <b>СОЛНЕЧНЫЕ КЫЛЬЯ:</b> У МКС есть огромные панели, которые делают ток из света! ⚡",
        "🧱 <b>КИРПИЧИ ИЗ ЛУНЫ:</b> Ученые хотят строить дома на Луне из лунной пыли! 🏗️",
        "🧨 <b>ПИРОБОЛТЫ:</b> Части ракеты отцепляются с помощью маленьких взрывов! 💥",
        "🛡️ <b>ТЕПЛОВОЙ ЩИТ:</b> Дно корабля защищает его от жара в 1500 градусов! 🔥",
        "🛰️ <b>КОСМИЧЕСКИЙ МУСОР:</b> Вокруг Земли летают тысячи обломков старых ракет! 🧹",
        "🎈 <b>ВАКУУМ:</b> В космосе нет воздуха, поэтому там нельзя дышать без шлема! 👨‍🚀",
        "🤖 <b>РОБОТЫ-ПОМОЩНИКИ:</b> На МКС живут роботы, у которых есть свои имена! 🤖",
        "🔭 <b>ЗОЛОТОЕ ЗЕРКАЛО:</b> У телескопа Уэбб зеркало покрыто настоящим золотом! ✨",
        "🌍 <b>СКОРОСТЬ ПУЛИ:</b> Чтобы выйти в космос, нужно лететь в 10 раз быстрее пули! 🚅",
        "💤 <b>СОН В СТАКАНЕ:</b> Космонавты спят в мешках, привязанных к стене! 😴",
        "🚿 <b>ВМЕСТО ДУША:</b> В космосе моются влажными полотенцами! 🧼",
        "🤐 <b>ТИШИНА:</b> В космосе абсолютная тишина, звук там не слышен! 🤫",
        "🍭 <b>ПЛАНЕТА-ЗЕФИРКА:</b> Существуют планеты такие легкие, что они плавали бы в ванне! 🍬",
        "🧊 <b>ЛЕДЯНЫЕ ЛУНЫ:</b> У Юпитера есть луна Европа, под льдом которой может быть океан! 🌊",
        "🧲 <b>МАГНИТНАЯ ЗАЩИТА:</b> Земля — это магнит, который защищает нас от лучей солнца! 🧲",
        "⏳ <b>РАЗНОЕ ВРЕМЯ:</b> В космосе время идет капельку иначе, чем на Земле! ⏳",
        "📡 <b>ПЕРВЫЙ СИГНАЛ:</b> Первый спутник просто передавал «Бип-бип», но это изменило мир! 📡",
        "👨‍🚀 <b>ЮРИЙ ГАГАРИН:</b> Его полет длился всего 108 минут! ⏱️",
        "⛽ <b>ЗАПРАВКА:</b> Корабли могут заправляться прямо на орбите! ⛽",
        "🎂 <b>ДЕНЬ РОЖДЕНИЯ:</b> Марсоход Curiosity сам спел себе песню на Марсе! 🎂"
    ]
    chosen_secret = random.choice(secrets_list)

    # Собираем текст 📝
    report = f"🚀 <b>СКОРО В КОСМОС: {rocket.upper()}</b>\n"
    report += f"🎯 <b>Миссия:</b> {mission_name}\n"
    report += f"⏳ <b>До старта:</b> {countdown}\n\n"
    report += f"📋 <b>Описание:</b> {description}\n\n"
    report += "--------------------------\n"
    report += f"🎒 <b>МАРТИ РАССКАЗЫВАЕТ:</b>\n{chosen_secret}\n"
    report += "--------------------------\n\n"
    
    # Добавляем видео, если оно есть 📺
    if video_url:
        report += f"📺 <b>Прямой эфир:</b> <a href='{video_url}'>Смотреть запуск</a>\n\n"
        
    report += "🌌 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    
    return report, launch_id, image_url, video_url

def send_to_telegram(text, photo_url):
    """Отправляем сообщение в Telegram 📤"""
    if photo_url:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': text, 'parse_mode': 'HTML'}
    else:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {'chat_id': CHANNEL_NAME, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
    
    requests.post(api_url, data=payload)

if __name__ == '__main__':
    print("--- 🏁 Начинаю проверку запусков ---")
    
    text_report, current_launch_id, photo_url, video_url = check_launches()
    
    print(f"📡 Получен ID запуска: {current_launch_id}")
    print(f"🎥 Найдена ссылка на видео: {video_url}") # Наш дебаг!
    
    if text_report and current_launch_id:
        sent_ids = load_sent_ids()
        print(f"🧠 В памяти уже есть: {sent_ids}")
        
        if current_launch_id not in sent_ids:
            print("🚀 Обнаружен новый запуск! Отправляю в Telegram...")
            send_to_telegram(text_report, photo_url)
            save_sent_id(current_launch_id)
            print("✅ Готово! Пост отправлен.")
        else:
            print("⏭️ Этот запуск уже был отправлен ранее.")
    else:
        print("❌ Не удалось получить данные.")
    
    print("--- 🏁 Проверка завершена ---")
