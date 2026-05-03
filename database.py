import psycopg2
import os

DB_URL = os.getenv('DATABASE_URL')

def get_connection():
    try:
        return psycopg2.connect(DB_URL, sslmode='require')
    except Exception as e:
        print(f"❌ Ошибка связи с базой: {e}")
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
        conn.commit()
        print("📡 [СИСТЕМА] База Supabase готова: опыт и память активны.")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
    finally:
        cursor.close()
        conn.close()

def add_xp(user_id, amount, username="Пилот"):
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, username, xp) 
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET xp = users.xp + EXCLUDED.xp, username = EXCLUDED.username
        ''', (user_id, username, amount))
        conn.commit()
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

def update_personal_log(user_id, new_info):
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET personal_log = personal_log || ' | ' || %s 
            WHERE user_id = %s
        ''', (new_info, user_id))
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
    if xp < 50: return "Кадет-наблюдатель 🐣"
    if xp < 150: return "Пилот-исследователь 🚀"
    if xp < 300: return "Старший штурман 🧭"
    if xp < 500: return "Командор орбиты 👨‍🚀"
    return "Адмирал Галактики 👑"
