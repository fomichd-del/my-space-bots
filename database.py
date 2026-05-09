import psycopg2
import os
import telebot
from datetime import datetime, timedelta

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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                xp INTEGER DEFAULT 0,
                personal_log TEXT DEFAULT ''
            )
        ''')
        new_columns = [
            ("spendable_dust", "INTEGER DEFAULT 0"),
            ("jackpot_claimed", "BOOLEAN DEFAULT FALSE"),
            ("streak_days", "INTEGER DEFAULT 0"),
            ("last_active_date", "TEXT DEFAULT ''"),
            ("game_node", "TEXT DEFAULT 'start'"),
            ("game_timer_end", "TIMESTAMP")
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
        print("📡 База данных синхронизирована.")
    except Exception as e:
        send_log(f"Ошибка инициализации БД: {e}")
    finally:
        cursor.close()
        conn.close()

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
    if not conn: return {"xp": 0, "spendable_dust": 0, "jackpot_claimed": False, "streak_days": 0}
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT xp, spendable_dust, jackpot_claimed, streak_days FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        if res:
            return {"xp": res[0], "spendable_dust": res[1], "jackpot_claimed": res[2], "streak_days": res[3]}
        return {"xp": 0, "spendable_dust": 0, "jackpot_claimed": False, "streak_days": 0}
    finally:
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
        current_date = datetime.now().strftime("%Y-%m-%d")
        cursor = conn.cursor()
        cursor.execute('SELECT last_active_date, streak_days FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        if not res: return 0
        last_date, streak = res
        if last_date == current_date: return streak
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
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
        # 🟢 ИСПРАВЛЕНО: Мощный фильтр от ботов, групп и самого Telegram
        cursor.execute('''
            SELECT username, xp 
            FROM users 
            WHERE user_id != 777000 
              AND user_id != 1087968824
              AND user_id > 0 
              AND username NOT ILIKE '%%bot%%' 
              AND username != 'Telegram'
              AND username != 'GroupAnonymousBot'
              AND username != 'Марти ученный'
              AND username != 'Group'
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

# --- НОВЫЕ ФУНКЦИИ ДЛЯ ИГРЫ ---

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
    try:
        finish_time = datetime.now() + timedelta(minutes=minutes)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET game_timer_end = %s WHERE user_id = %s', (finish_time, user_id))
        conn.commit()
    finally:
        cursor.close()
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

# ==========================================
# 🌿 МОДУЛЬ ЭКО-ОТСЕКА (ТАМАГОЧИ)
# ==========================================
import json

def setup_eco_bay():
    conn = get_connection()
    cursor = conn.cursor()
    columns = [
        ("pet_level", "INTEGER DEFAULT 1"),
        ("pet_hunger", "INTEGER DEFAULT 50"),
        ("pet_clean", "INTEGER DEFAULT 50"),
        ("pet_happiness", "INTEGER DEFAULT 50"),
        ("pet_items", "TEXT DEFAULT ''"),
        ("pet_xp", "INTEGER DEFAULT 0"),
        ("pet_date", "TEXT DEFAULT ''"),
        ("pet_feed_count", "INTEGER DEFAULT 0"),
        ("pet_clean_count", "INTEGER DEFAULT 0"),
        ("pet_play_count", "INTEGER DEFAULT 0"),
        ("pet_count", "INTEGER DEFAULT 1"),      # 🟢 Кол-во улиток (1, 2 или 3)
        ("pet_status", "TEXT DEFAULT 'alive'"),  # 🟢 Статус: alive или dead
        ("pet_colors", "TEXT DEFAULT 'blue'")    # 🟢 Цвета (например: "blue, red, purple")
    ]
    for col_name, col_type in columns:
        try: cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"); conn.commit()
        except: conn.rollback() 
    cursor.close()
    conn.close()

def get_pet_data(user_id):
    conn = get_connection()
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
    return {"level": 1, "hunger": 50, "clean": 50, "happiness": 50, "items": [], "xp": 0, "date": "", "feed_count": 0, "clean_count": 0, "play_count": 0, "count": 1, "status": "alive", "colors": "blue"}

def update_pet_data(user_id, p):
    conn = get_connection()
    cursor = conn.cursor()
    items_str = ",".join([i for i in p['items'] if i.strip()])
    cursor.execute("""
        UPDATE users SET pet_level=%s, pet_hunger=%s, pet_clean=%s, pet_happiness=%s, pet_items=%s, 
        pet_xp=%s, pet_date=%s, pet_feed_count=%s, pet_clean_count=%s, pet_play_count=%s,
        pet_count=%s, pet_status=%s, pet_colors=%s WHERE user_id=%s
    """, (p['level'], p['hunger'], p['clean'], p['happiness'], items_str, p['xp'], p['date'], p['feed_count'], p['clean_count'], p['play_count'], p['count'], p['status'], p['colors'], user_id))
    conn.commit()
    conn.close()

def get_all_users_with_pets():
    """Собирает данные всех пилотов, у которых есть живой Эко-отсек"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Достаем ID, дату последнего входа, сытость и чистоту
        cursor.execute("SELECT user_id, pet_date, pet_hunger, pet_clean FROM users WHERE pet_status = 'alive'")
        res = cursor.fetchall()
    except:
        res = []
    conn.close()
    return res

# ==========================================
# 📰 МОДУЛЬ НОВОСТЕЙ КАНАЛА
# ==========================================

def setup_news_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS channel_news (date TEXT, content TEXT);")
        conn.commit()
    except Exception as e:
        print(f"Ошибка создания таблицы новостей: {e}")
    cursor.close()
    conn.close()

def add_news(date, text):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO channel_news (date, content) VALUES (%s, %s)", (date, text))
    conn.commit()
    conn.close()

def get_today_news(date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM channel_news WHERE date = %s", (date,))
    res = cursor.fetchall()
    conn.close()
    return [r[0] for r in res]

def get_all_user_ids():
    """Достает ID всех пилотов, когда-либо запускавших бота"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    res = cursor.fetchall()
    conn.close()
    return [r[0] for r in res]
