import psycopg2
import os

DB_URL = os.getenv('DATABASE_URL')

def get_connection():
    try:
        # Обязательно используем sslmode='require' для стабильной связи с Supabase
        return psycopg2.connect(DB_URL, sslmode='require')
    except Exception as e:
        print(f"❌ Ошибка связи с базой: {e}")
        return None

def init_db():
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        # 1. Создаем таблицу, если её нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                xp INTEGER DEFAULT 0,
                personal_log TEXT DEFAULT ''
            )
        ''')
        
        # 2. ПРОВЕРКА: Добавляем колонку personal_log, если таблица уже была, но без неё
        cursor.execute('''
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='users' AND column_name='personal_log') THEN 
                    ALTER TABLE users ADD COLUMN personal_log TEXT DEFAULT '';
                END IF; 
            END $$;
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
    except Exception as e:
        print(f"❌ Ошибка начисления XP: {e}")
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
    """Добавляет новую информацию в бортовой журнал пилота"""
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET personal_log = CASE 
                WHEN personal_log IS NULL OR personal_log = '' THEN %s 
                ELSE personal_log || ' | ' || %s 
            END
            WHERE user_id = %s
        ''', (new_info, new_info, user_id))
        conn.commit()
    except Exception as e:
        print(f"❌ Ошибка обновления лога: {e}")
    finally:
        cursor.close()
        conn.close()

def get_personal_log(user_id):
    """Получает историю журнала пилота"""
    conn = get_connection()
    if not conn: return ""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT personal_log FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        return res[0] if res and res[0] else "Данных пока нет. Начните исследование!"
    finally:
        cursor.close()
        conn.close()

# === ОБНОВЛЕННАЯ СИСТЕМА ЗВАНИЙ АКАДЕМИИ ===
def get_rank_name(xp):
    if xp < 5: return "Космический Кадет 🚀"
    if xp < 12: return "Навигатор Орбиты 🛰"
    if xp < 20: return "Бортинженер 🔧"
    if xp < 30: return "Астро-Исследователь 🔭"
    if xp < 45: return "Учёный Пилот 🪐"
    if xp < 65: return "Капитан Корабля 🛸"
    if xp < 90: return "Командор Галактики 🎖"
    if xp < 120: return "Адмирал Флота ⭐"
    if xp < 160: return "Академик Космоса 🎓"
    return "Верный Помощник Марти 🐕"
