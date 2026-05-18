import psycopg2
import os
import telebot
import random
from datetime import datetime, timedelta

# --- ДОБАВЛЕННАЯ ФУНКЦИЯ ДЛЯ СИНХРОНИЗАЦИИ ВРЕМЕНИ ---
def get_ship_date():
    """Возвращает текущую дату для Чернигова (UTC+3)"""
    return (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d")

TOKEN = os.getenv('MARTY_BOT_TOKEN')
bot_log = telebot.TeleBot(TOKEN)
LOG_CHAT_ID = "-1003756164148"

def send_log(error_text):
    try:
        bot_log.send_message(LOG_CHAT_ID, f"🗄 **ОШИБКА БАЗЫ ДАННЫХ:**\n`{error_text}`", parse_mode="Markdown")
    except: pass

DB_URL = os.getenv('DATABASE_URL')

def get_connection():
    try:
        return psycopg2.connect(DB_URL, sslmode='require')
    except Exception as e:
        send_log(f"Ошибка связи с базой: {e}")
        return None

def init_db():
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        # 1. Создаем таблицу пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                xp INTEGER DEFAULT 0,
                personal_log TEXT DEFAULT ''
            )
        ''')
        
        # 2. Добавляем все нужные колонки (ваш существующий цикл)
        new_columns = [
            ("spendable_dust", "INTEGER DEFAULT 0"),
            ("jackpot_claimed", "BOOLEAN DEFAULT FALSE"),
            ("streak_days", "INTEGER DEFAULT 0"),
            ("last_active_date", "TEXT DEFAULT ''"),
            ("game_node", "TEXT DEFAULT 'start'"),
            ("game_timer_end", "TIMESTAMP"),
            ("last_interact", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"),
            ("silence_until", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"),
            ("last_vision_context", "TEXT DEFAULT ''"),
            ("last_vision_time", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"),
            ("dog_equipped", "TEXT DEFAULT ''"),
            ("dog_profession", "TEXT DEFAULT 'Кадет'"),
            ("last_quiz_date", "TEXT DEFAULT ''")
            ("dog_last_exp", "TEXT DEFAULT ''")
        ]
        
        for col_name, col_type in new_columns:
            cursor.execute(f'''
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='users' AND column_name='{col_name}') THEN 
                        ALTER TABLE users ADD COLUMN {col_name} {col_type};
                    END IF; 
                END $$;
            ''')
        
        conn.commit()
        print("📡 Таблица пользователей синхронизирована.")
        
        # --- ВОТ ТА САМАЯ МЕЛКАЯ ПРАВКА ---
        # Теперь прямо отсюда вызываем создание таблицы новостей и эко-отсека
        setup_news_db()
        setup_eco_bay()
        # ----------------------------------

    except Exception as e:
        send_log(f"Ошибка инициализации БД: {e}")
    finally:
        cursor.close()
        conn.close()

# --- КРАТКОСРОЧНАЯ ПАМЯТЬ ЗРЕНИЯ ---

def save_vision_context(user_id, context_text):
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET last_vision_context = %s, last_vision_time = CURRENT_TIMESTAMP 
            WHERE user_id = %s
        ''', (context_text, user_id))
        conn.commit()
    except Exception as e:
        send_log(f"Ошибка сохранения памяти зрения: {e}")
    finally:
        cursor.close()
        conn.close()

def get_vision_context(user_id):
    conn = get_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT last_vision_context 
            FROM users 
            WHERE user_id = %s 
              AND last_vision_time > NOW() - INTERVAL '30 minutes'
              AND last_vision_context != ''
        ''', (user_id,))
        res = cursor.fetchone()
        return res[0] if res else None
    except Exception as e:
        send_log(f"Ошибка чтения памяти зрения: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def clear_vision_context(user_id):
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_vision_context = '' WHERE user_id = %s", (user_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# --- ФУНКЦИИ АКТИВНОСТИ ПИЛОТОВ ---

def update_last_active(user_id):
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_interact = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def set_silence(user_id, hours=12):
    conn = get_connection()
    if not conn: return
    try:
        until = datetime.now() + timedelta(hours=hours)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET silence_until = %s WHERE user_id = %s", (until, user_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_users_for_ping():
    conn = get_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id FROM users 
            WHERE (last_interact > NOW() - INTERVAL '24 hours' OR last_interact < NOW() - INTERVAL '3 days')
            AND silence_until < NOW()
            AND user_id > 0
            LIMIT 10
        """)
        res = cursor.fetchall()
        return [r[0] for r in res]
    finally:
        cursor.close()
        conn.close()

# --- ФУНКЦИИ ПРОФИЛЯ И ОПЫТА ---

def add_xp(user_id, amount, username="Пилот"):
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, username, xp, spendable_dust) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                xp = users.xp + EXCLUDED.xp, 
                spendable_dust = users.spendable_dust + EXCLUDED.spendable_dust,
                username = EXCLUDED.username
        ''', (user_id, username, amount, amount))
        conn.commit()
    except Exception as e:
        send_log(f"Ошибка начисления XP: {e}")
    finally:
        cursor.close()
        conn.close()

def is_user_new(user_id):
    """Проверяет, есть ли пилот в базе данных (True - если новый, False - если уже был)"""
    conn = get_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
        # Если ничего не нашли, значит пилот новый (вернут True)
        return cursor.fetchone() is None
    finally:
        cursor.close()
        conn.close()

def get_user_stats(user_id):
    conn = get_connection()
    if not conn: return 0
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT xp FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        return res[0] if res else 0
    finally:
        cursor.close()
        conn.close()

def get_user_data(user_id):
    conn = get_connection()
    if not conn: return {"xp": 0, "spendable_dust": 0, "jackpot_claimed": False, "streak_days": 0, "name": "Пилот"}
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT xp, spendable_dust, jackpot_claimed, streak_days, username FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        if res:
            return {"xp": res[0], "spendable_dust": res[1], "jackpot_claimed": res[2], "streak_days": res[3], "name": res[4]}
        return {"xp": 0, "spendable_dust": 0, "jackpot_claimed": False, "streak_days": 0, "name": "Пилот"}
    finally:
        cursor.close()
        conn.close()

def update_user_data(user_id, u_data):
    """Сохраняет обновленные данные пользователя (опыт, пыль, стрик) обратно в базу"""
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET xp = %s, 
                spendable_dust = %s, 
                jackpot_claimed = %s, 
                streak_days = %s
            WHERE user_id = %s
        ''', (u_data['xp'], u_data['spendable_dust'], u_data['jackpot_claimed'], u_data['streak_days'], user_id))
        conn.commit()
    except Exception as e:
        send_log(f"Ошибка сохранения данных пилота: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

def set_jackpot_claimed(user_id):
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET jackpot_claimed = TRUE WHERE user_id = %s', (user_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def spend_dust(user_id, amount):
    conn = get_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET spendable_dust = spendable_dust - %s WHERE user_id = %s AND spendable_dust >= %s', (amount, user_id, amount))
        if cursor.rowcount > 0:
            conn.commit()
            return True
        return False
    finally:
        cursor.close()
        conn.close()

def check_and_update_streak(user_id):
    conn = get_connection()
    if not conn: return 0
    try:
        current_date = get_ship_date()
        cursor = conn.cursor()
        cursor.execute('SELECT last_active_date, streak_days FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        if not res: return 0
        last_date, streak = res
        if last_date == current_date: return streak
        yesterday = (datetime.now() + timedelta(hours=3) - timedelta(days=1)).strftime("%Y-%m-%d")
        new_streak = streak + 1 if last_date == yesterday else 1
        cursor.execute('UPDATE users SET last_active_date = %s, streak_days = %s WHERE user_id = %s', (current_date, new_streak, user_id))
        conn.commit()
        return new_streak
    finally:
        cursor.close()
        conn.close()

def get_top_pilots(limit=5):
    conn = get_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, xp 
            FROM users 
            WHERE user_id > 0 
              AND user_id NOT IN (777000, 1087968824)
              AND username NOT ILIKE '%%bot%%' 
              AND username NOT IN ('Telegram', 'GroupAnonymousBot', 'Марти ученный', 'Group')
            ORDER BY xp DESC 
            LIMIT %s
        ''', (limit,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def update_personal_log(user_id, new_info):
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('''UPDATE users SET personal_log = CASE WHEN personal_log IS NULL OR personal_log = '' THEN %s ELSE personal_log || ' | ' || %s END WHERE user_id = %s''', (new_info, new_info, user_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_personal_log(user_id):
    conn = get_connection()
    if not conn: return ""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT personal_log FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        return res[0] if res and res[0] else "Данных пока нет."
    finally:
        cursor.close()
        conn.close()

def get_rank_name(xp):
    if xp < 15: return "Космический Кадет 🚀"
    if xp < 40: return "Навигатор Орбиты 🛰"
    if xp < 80: return "Бортинженер 🔧"
    if xp < 130: return "Астро-Исследователь 🔭"
    if xp < 200: return "Учёный Пилот 🪐"
    if xp < 300: return "Капитан Корабля 🛸"
    if xp < 450: return "Командор Галактики 🎖"
    if xp < 650: return "Адмирал Флота ⭐"
    if xp < 900: return "Академик Космоса 🎓"
    return "Верный Помощник Марти 🐕"

# --- ИГРОВОЙ МОДУЛЬ ---

def update_game_progress(user_id, node_id):
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET game_node = %s WHERE user_id = %s', (node_id, user_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def set_game_timer(user_id, minutes):
    conn = get_connection()
    if not conn: return
    
    cursor = None # Заранее создаем переменную, чтобы finally не ругался
    try:
        # 🛡 БРОНЕЖИЛЕТ: Принудительно превращаем текст "15" в число 15
        minutes_int = int(minutes) 
        
        finish_time = datetime.now() + timedelta(minutes=minutes_int)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET game_timer_end = %s WHERE user_id = %s', (finish_time, user_id))
        conn.commit()
        
    except Exception as e:
        # Если что-то пойдет не так, мы это увидим, а бот не зависнет
        send_log(f"Ошибка таймера: {e}")
        print(f"🚨 ОШИБКА БД (таймер): {e}")
        
    finally:
        if cursor: 
            cursor.close()
        if conn:
            conn.close()

def get_game_status(user_id):
    conn = get_connection()
    if not conn: return "start", None
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT game_node, game_timer_end FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        return res if res else ("start", None)
    finally:
        cursor.close()
        conn.close()

# --- ЭКО-ОТCЕК ---

def setup_eco_bay():
    conn = get_connection()
    if not conn: return
    columns = [
        "pet_level INTEGER DEFAULT 1", "pet_hunger INTEGER DEFAULT 50",
        "pet_clean INTEGER DEFAULT 50", "pet_happiness INTEGER DEFAULT 50",
        "pet_items TEXT DEFAULT ''", "pet_xp INTEGER DEFAULT 0",
        "pet_date TEXT DEFAULT ''", "pet_feed_count INTEGER DEFAULT 0",
        "pet_clean_count INTEGER DEFAULT 0", "pet_play_count INTEGER DEFAULT 0",
        "pet_count INTEGER DEFAULT 1", "pet_status TEXT DEFAULT 'alive'",
        "pet_colors TEXT DEFAULT 'blue'"
    ]
    try:
        cursor = conn.cursor()
        for col in columns:
            cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col};")
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_pet_data(user_id):
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor()
    cursor.execute("""SELECT pet_level, pet_hunger, pet_clean, pet_happiness, pet_items, 
                      pet_xp, pet_date, pet_feed_count, pet_clean_count, pet_play_count,
                      pet_count, pet_status, pet_colors FROM users WHERE user_id = %s""", (user_id,))
    res = cursor.fetchone()
    conn.close()
    if res:
        return {
            "level": res[0], "hunger": res[1], "clean": res[2], "happiness": res[3],
            "items": res[4].split(",") if res[4] else [],
            "xp": res[5], "date": res[6], "feed_count": res[7], "clean_count": res[8], "play_count": res[9],
            "count": res[10], "status": res[11], "colors": res[12]
        }
    return None

def update_pet_data(user_id, p):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    h, c, hap = min(100, max(0, p['hunger'])), min(100, max(0, p['clean'])), min(100, max(0, p['happiness']))
    items_str = ",".join([i for i in p['items'] if i.strip()])
    cursor.execute("""
        UPDATE users SET pet_level=%s, pet_hunger=%s, pet_clean=%s, pet_happiness=%s, pet_items=%s, 
        pet_xp=%s, pet_date=%s, pet_feed_count=%s, pet_clean_count=%s, pet_play_count=%s,
        pet_count=%s, pet_status=%s, pet_colors=%s WHERE user_id=%s
    """, (p['level'], h, c, hap, items_str, p['xp'], p['date'], p['feed_count'], p['clean_count'], p['play_count'], p['count'], p['status'], p['colors'], user_id))
    conn.commit()
    conn.close()

def get_all_users_with_pets():
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, pet_date, pet_hunger, pet_clean FROM users WHERE pet_status = 'alive'")
    res = cursor.fetchall()
    conn.close()
    return res

# --- ПУДЕЛЬ (ГАРДЕРОБ И ВЫГУЛ) ---

def get_dog_data(user_id):
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor()
    # 🟢 Добавили dog_last_exp в SELECT
    cursor.execute("""SELECT dog_level, dog_hunger, dog_energy, dog_mood, dog_items, 
                      dog_xp, dog_date, dog_status, dog_equipped, dog_last_exp FROM users WHERE user_id = %s""", (user_id,))
    res = cursor.fetchone()
    conn.close()
    if res:
        return {
            "level": res[0], "hunger": res[1], "energy": res[2], "mood": res[3],
            "items": res[4].split(",") if res[4] else [],
            "xp": res[5], "date": res[6], "status": res[7],
            "equipped": res[8].split(",") if res[8] else [],
            "last_exp": res[9] if res[9] else "" # 🟢 Записываем в словарь
        ]
    return None

def update_dog_data(user_id, d):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    h, e, m = min(100, max(0, d['hunger'])), min(100, max(0, d['energy'])), min(100, max(0, d['mood']))
    items_str = ",".join([i for i in d['items'] if i.strip()])
    equipped_str = ",".join([i for i in d.get('equipped', []) if i.strip()])
    
    # 🟢 Добавили dog_last_exp=%s в UPDATE
    cursor.execute("""
        UPDATE users SET dog_level=%s, dog_hunger=%s, dog_energy=%s, dog_mood=%s, 
        dog_items=%s, dog_xp=%s, dog_date=%s, dog_status=%s, dog_equipped=%s, dog_last_exp=%s WHERE user_id=%s
    """, (d['level'], h, e, m, items_str, d['xp'], d['date'], d['status'], equipped_str, d.get('last_exp', ''), user_id))
    conn.commit()
    conn.close()

def equip_dog_item(user_id, item_name):
    """Надеть вещь на Марти"""
    d = get_dog_data(user_id)
    if not d or item_name not in d['items']: return False
    if item_name not in d['equipped']:
        d['equipped'].append(item_name)
        update_dog_data(user_id, d)
        return True
    return False

def unequip_dog_item(user_id, item_name):
    """Снять вещь с Марти"""
    d = get_dog_data(user_id)
    if not d or item_name not in d['equipped']: return False
    d['equipped'].remove(item_name)
    update_dog_data(user_id, d)
    return True

def process_dog_walk(user_id):
    """Выгулять Марти за 10 пыли"""
    if not spend_dust(user_id, 10): return "low_dust"
    d = get_dog_data(user_id)
    if not d: return "error"
    d['mood'] = 100
    d['energy'] = min(100, d['energy'] + 30)
    bonus_xp = 0
    if random.random() < 0.2: # 20% шанс найти бонус
        bonus_xp = random.randint(5, 15)
        d['xp'] += bonus_xp
        add_xp(user_id, bonus_xp)
    update_dog_data(user_id, d)
    return bonus_xp if bonus_xp > 0 else "success"

# --- НОВОСТИ (УЛУЧШЕННЫЙ ОТСЕК) ---

def setup_news_db():
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        # Добавляем UNIQUE на content, чтобы одна и та же новость не дублировалась
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_news (
                id SERIAL PRIMARY KEY,
                date TEXT, 
                content TEXT UNIQUE
            );
        ''')
        conn.commit()
    except Exception as e:
        send_log(f"Ошибка создания таблицы новостей: {e}")
    finally:
        cursor.close()
        conn.close()

def add_news(date, text):
    """Сохраняет новость. Если такая уже есть — просто игнорирует (благодаря ON CONFLICT)"""
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO channel_news (date, content) 
            VALUES (%s, %s)
            ON CONFLICT (content) DO NOTHING
        ''', (date, text))
        conn.commit()
    except Exception as e:
        send_log(f"Ошибка записи новости: {e}")
    finally:
        cursor.close()
        conn.close()

def get_today_news(date):
    """Возвращает список уникальных новостей за указанную дату"""
    conn = get_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        # Используем DISTINCT для страховки от дублей
        cursor.execute("SELECT DISTINCT content FROM channel_news WHERE date = %s", (date,))
        res = cursor.fetchall()
        return [r[0] for r in res] # Возвращаем результат здесь
    except Exception as e:
        send_log(f"Ошибка чтения новостей: {e}")
        return []
    finally:
        # Ресурсы всегда закрываются после return в блоке try
        if conn:
            cursor.close()
            conn.close()

def get_all_user_ids():
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id > 0")
    res = cursor.fetchall()
    conn.close()
    return [r[0] for r in res]

def get_dog_profession(user_id):
    """Получает текущую профессию Марти из базы."""
    conn = get_connection()
    if not conn: return 'Кадет'
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT dog_profession FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else 'Кадет'
    except:
        return 'Кадет'
    finally:
        if conn:
            cursor.close()
            conn.close()

def set_dog_profession(user_id, profession_name):
    """Записывает выбранную профессию в базу."""
    conn = get_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET dog_profession = %s WHERE user_id = %s", (profession_name, user_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка записи профессии: {e}")
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()

def check_and_update_quiz(user_id, today_date):
    """Проверяет, участвовал ли пилот в викторине сегодня."""
    conn = get_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT last_quiz_date FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        if result and result[0] == today_date:
            return False 
            
        cursor.execute("UPDATE users SET last_quiz_date = %s WHERE user_id = %s", (today_date, user_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка викторины в БД: {e}")
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()

def is_user_new(user_id):
    """Проверяет, является ли пилот новым."""
    conn = get_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone() is None
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    # Эта команда запустится только если вы запустите сам файл database.py
    # Она создаст все таблицы и колонки, если их еще нет.
    init_db() 
    print("✅ Все системы базы данных инициализированы!")
