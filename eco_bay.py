import time
import urllib.parse
import requests
from datetime import datetime
from telebot import types as tele_types
from database import get_pet_data, update_pet_data, spend_dust, get_user_data

SHOP_ITEMS = {
    "neon_rocks": {"name": "Светящиеся камни", "prompt": "glowing neon cosmic rocks", "price": 10},
    "alien_castle": {"name": "Замок НЛО", "prompt": "miniature crashed UFO castle", "price": 25},
    "disco_ball": {"name": "Звездный диско-шар", "prompt": "tiny floating space disco ball", "price": 15}
}

def get_dynamic_image_url(pet, user_id):
    if pet['status'] == 'dead':
        # 💀 Визуал смерти
        prompt = "empty dirty glass terrarium, broken glass, dried moss, dark gloomy lighting, depressing atmosphere, no life"
        return f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={user_id}&nofeed=true"

    base = f"macro photography of {pet['count']} cute alien space snails, {pet['colors']} shells, high-tech glass terrarium"
    
    # 1. Состояние
    if pet['clean'] < 30: state = "murky green dirty water, messy environment, withered moss"
    else: state = "clean crystal clear water, glowing neon moss, bubbles"
        
    # 2. Вид (по уровню)
    if pet['level'] < 5: evo = "baby snails"
    elif pet['level'] < 15: evo = "majestic cosmic snails with nebula patterns"
    else: evo = "god-like ancient star snails, galactic aura"
        
    decor = [SHOP_ITEMS[k]["prompt"] for k in pet['items'] if k in SHOP_ITEMS]
    decor_prompt = "decorated with " + " and ".join(decor) if decor else ""
        
    eng_prompt = f"{base}, {evo}, {state}, {decor_prompt}, 4k, cinematic lighting"
    seed = int(time.time() / 3600) + user_id
    return f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng_prompt)}?width=1024&height=1024&nologo=true&seed={seed}&nofeed=true"

def check_daily_decay(pet):
    today = datetime.now().strftime("%Y-%m-%d")
    if pet['date'] != today and pet['status'] == 'alive':
        pet['hunger'] = max(0, pet['hunger'] - 30)
        pet['clean'] = max(0, pet['clean'] - 20)
        pet['happiness'] = max(0, pet['happiness'] - 25)
        pet['feed_count'] = 0
        pet['clean_count'] = 0
        pet['play_count'] = 0
        pet['date'] = today
        # ⚠️ ПРОВЕРКА НА СМЕРТЬ
        if pet['hunger'] <= 0 or pet['clean'] <= 0:
            pet['status'] = 'dead'
    return pet

def send_eco_menu(bot, chat_id, user_id):
    pet = check_daily_decay(get_pet_data(user_id))
    update_pet_data(user_id, pet)
    u_data = get_user_data(user_id)
    url = get_dynamic_image_url(pet, user_id)
    
    if pet['status'] == 'dead':
        text = "💀 **ТРАГЕДИЯ В ЭКО-ОТСЕКЕ**\n\nПилот, из-за ненадлежащего ухода эко-система погибла. Террариум заброшен.\n\nНужна полная дезинфекция!"
        kb = tele_types.InlineKeyboardMarkup()
        kb.add(tele_types.InlineKeyboardButton("🧼 Дезинфекция (-50 💰)", callback_data="eco_sanitize"))
    else:
        # Умножаем стоимость на кол-во улиток (Синдикат)
        f_cost, c_cost, p_cost = 2*pet['count'], 3*pet['count'], 2*pet['count']
        text = (
            f"🌿 **ЭКО-ОТСЕК (Жильцов: {pet['count']})**\n"
            f"🧬 Уровень: {pet['level']} | Опыт: {pet['xp']}/10\n"
            f"🔋 Сытость: {pet['hunger']}% | 💧 Чистота: {pet['clean']}% | 🎾 Радость: {pet['happiness']}%\n\n"
            f"💰 _Пыль: {u_data['spendable_dust']} ед._"
        )
        kb = tele_types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            tele_types.InlineKeyboardButton(f"🥬 Кормить (-{f_cost} 💰)", callback_data="eco_feed"),
            tele_types.InlineKeyboardButton(f"🧽 Убрать (-{c_cost} 💰)", callback_data="eco_clean"),
            tele_types.InlineKeyboardButton(f"🎾 Играть (-{p_cost} 💰)", callback_data="eco_play"),
            tele_types.InlineKeyboardButton("🛒 Магазин", callback_data="eco_shop")
        )
        if pet['level'] >= 15:
            if pet['count'] == 1: kb.add(tele_types.InlineKeyboardButton("➕ Найти пару (-300 💰)", callback_data="eco_addpet"))
            elif pet['count'] == 2: kb.add(tele_types.InlineKeyboardButton("🥚 Вывести потомство (-500 💰)", callback_data="eco_addpet"))

    try:
        # Марти пытается скачать картинку
        img_data = requests.get(url, timeout=20).content 
        # И отправить её как файл, а не как ссылку
        bot.send_photo(chat_id, img_data, caption=text, parse_mode="Markdown", reply_markup=kb)
    except Exception as e:
        # Если не вышло — прислать хотя бы текст
        print(f"Ошибка отправки фото: {e}")
        bot.send_message(chat_id, text + "\n\n⚠️ _Сбой визуализации террариума!_", reply_markup=kb)

def handle_eco_callback(bot, call):
    user_id = call.from_user.id
    action = call.data.replace("eco_", "")
    pet = check_daily_decay(get_pet_data(user_id))
    
    if action == "sanitize":
        if spend_dust(user_id, 50):
            new_pet = {"level": 1, "hunger": 100, "clean": 100, "happiness": 100, "items": [], "xp": 0, "date": datetime.now().strftime("%Y-%m-%d"), "feed_count": 0, "clean_count": 0, "play_count": 0, "count": 1, "status": "alive", "colors": "blue"}
            update_pet_data(user_id, new_pet)
            bot.answer_callback_query(call.id, "🧼 Стерилизация завершена! Заселена новая улитка.", show_alert=True)
        else: bot.answer_callback_query(call.id, "❌ Нужно 50 Пыли!", show_alert=True)
    
    elif action == "addpet":
        cost = 300 if pet['count'] == 1 else 500
        if spend_dust(user_id, cost):
            pet['count'] += 1
            # Генетика: добавляем новый цвет в палитру
            new_color = "red" if pet['count'] == 2 else "purple"
            pet['colors'] += f", {new_color}"
            update_pet_data(user_id, pet)
            bot.answer_callback_query(call.id, "💖 Пополнение в семействе!", show_alert=True)
        else: bot.answer_callback_query(call.id, f"❌ Нужно {cost} Пыли!", show_alert=True)

    # ... логика feed, clean, play такая же, как раньше, но с умножением цены (cost * pet['count'])
    
    bot.delete_message(call.message.chat.id, call.message.message_id)

    from threading import Thread

# Глобальный словарь, чтобы Марти не спамил напоминаниями каждую секунду
sent_reminders = {}

def run_reminder_loop(bot):
    """Автономный сканер Эко-отсеков. Крутится в фоне."""
    def loop():
        while True:
            try:
                from database import get_all_users_with_pets
                users = get_all_users_with_pets()
                today = datetime.now().strftime("%Y-%m-%d")
                
                for row in users:
                    user_id, pet_date, hunger, clean = row
                    
                    # Если сегодня уже напоминали — пропускаем
                    if sent_reminders.get(user_id) == today:
                        continue
                        
                    # Марти бьет тревогу, если пилот сегодня не заходил (pet_date != today)
                    # или если показатели уже критически низкие (меньше 40)
                    if pet_date != today or hunger <= 40 or clean <= 40:
                        try:
                            text = (
                                "🐾 **БОРТОВОЕ НАПОМИНАНИЕ ОТ МАРТИ**\n\n"
                                "Прием, Командор! Сканеры фиксируют падение показателей в твоем террариуме. "
                                "Улитки скучают, а уровень загрязнения растет.\n\n"
                                "Срочно зайди в **🌿 Эко-отсек**, чтобы навести порядок, иначе эко-система погибнет! Прием!"
                            )
                            bot.send_message(user_id, text, parse_mode="Markdown")
                            # Записываем, что сегодня этому пилоту уже напомнили
                            sent_reminders[user_id] = today
                        except Exception as e:
                            pass # Если пилот заблокировал бота, просто игнорируем
            except Exception as e:
                print(f"Ошибка радара Эко-отсека: {e}")
            
            # Радар засыпает на 4 часа (14400 секунд), затем проверяет снова
            time.sleep(14400)
    
    # Запускаем бесконечный цикл в отдельном независимом потоке
    Thread(target=loop, daemon=True).start()
    send_eco_menu(bot, call.message.chat.id, user_id)
