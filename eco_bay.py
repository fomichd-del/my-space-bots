import time
import urllib.parse
from telebot import types as tele_types
from database import get_pet_data, update_pet_data, spend_dust, get_user_data

def get_dynamic_image_url(level, hunger, clean, user_id):
    """Генерирует промпт на основе состояния террариума"""
    base = "macro photography of a cute alien space snail in a high-tech glass terrarium, 4k, cinematic lighting, vivid colors"
    
    # 1. Состояние эко-системы
    if hunger < 40 or clean < 40:
        state = "dirty water, messy environment, gloomy dim lighting, sad mood, withered alien moss"
    else:
        state = "clean crystal clear water, glowing neon moss, magical bright atmosphere, happy vibe, floating bubbles"
        
    # 2. Эволюция (Уровень)
    if level < 3:
        evo = "small baby snail, tiny glowing shell"
    elif level < 6:
        evo = "majestic adult snail, bright nebula shell, floating mini asteroids"
    else:
        evo = "giant god-like cosmic snail, entire galaxy inside its shell, epic sci-fi laboratory background"
        
    eng_prompt = f"{base}, {evo}, {state}"
    seed = int(time.time()) + user_id # Всегда новая уникальная картинка
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng_prompt)}?width=1024&height=1024&nologo=true&seed={seed}&nofeed=true"
    return url

def send_eco_menu(bot, chat_id, user_id):
    pet = get_pet_data(user_id)
    u_data = get_user_data(user_id)
    
    # Уменьшаем параметры со временем (имитация жизни). 
    # В идеале это делать по таймеру, но для простоты отнимаем по чуть-чуть при каждом входе.
    new_hunger = max(0, pet['hunger'] - 5)
    new_clean = max(0, pet['clean'] - 5)
    update_pet_data(user_id, pet['level'], new_hunger, new_clean)
    
    url = get_dynamic_image_url(pet['level'], new_hunger, new_clean, user_id)
    
    # Формируем рапорт Марти
    status = "🟢 Идеально" if new_hunger > 50 and new_clean > 50 else "🔴 Требует ухода!"
    text = (
        f"🌿 **ЭКО-ОТСЕК (Террариум)**\n\n"
        f"Пилот, твоя Лунная Улитка эволюционирует! Поддерживай чистоту и корми её астероидным мхом.\n\n"
        f"🧬 **Уровень развития:** {pet['level']}\n"
        f"🔋 **Сытость:** {new_hunger}%\n"
        f"💧 **Чистота:** {new_clean}%\n"
        f"📊 **Статус:** {status}\n\n"
        f"💰 _Твой баланс: {u_data['spendable_dust']} пыли._"
    )
    
    kb = tele_types.InlineKeyboardMarkup()
    kb.row(tele_types.InlineKeyboardButton("🥬 Кормить (-2 💰)", callback_data="eco_feed"),
           tele_types.InlineKeyboardButton("🧽 Убрать (-3 💰)", callback_data="eco_clean"))
    kb.row(tele_types.InlineKeyboardButton(f"🔬 Эволюция (-20 💰)", callback_data="eco_upgrade"))
    
    bot.send_photo(chat_id, url, caption=text, parse_mode="Markdown", reply_markup=kb)

def handle_eco_callback(bot, call):
    user_id = call.from_user.id
    action = call.data.split('_')[1]
    pet = get_pet_data(user_id)
    
    if action == "feed":
        if spend_dust(user_id, 2):
            update_pet_data(user_id, pet['level'], pet['hunger'] + 30, pet['clean'])
            bot.answer_callback_query(call.id, "🥬 Улитка покормлена! Сытость +30%", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает Звездной Пыли!", show_alert=True)
            return
            
    elif action == "clean":
        if spend_dust(user_id, 3):
            update_pet_data(user_id, pet['level'], pet['hunger'], pet['clean'] + 40)
            bot.answer_callback_query(call.id, "🧽 Террариум сияет! Чистота +40%", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает Звездной Пыли!", show_alert=True)
            return
            
    elif action == "upgrade":
        if spend_dust(user_id, 20):
            update_pet_data(user_id, pet['level'] + 1, 100, 100) # При эволюции полностью лечим
            bot.answer_callback_query(call.id, "🌌 ЭВОЛЮЦИЯ! Уровень повышен!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает Звездной Пыли (нужно 20)!", show_alert=True)
            return

    # Перерисовываем меню после действия
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_eco_menu(bot, call.message.chat.id, user_id)
