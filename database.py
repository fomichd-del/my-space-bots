import psycopg2
import os
from datetime import datetime, timedelta

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
        
        # БЕЗОПАСНОЕ ОБНОВЛЕНИЕ БАЗЫ: Добавляем новые колонки для геймификации
        new_columns = [
            ("spendable_dust", "INTEGER DEFAULT 0"), # Кошелек для покупок
            ("jackpot_claimed", "BOOLEAN DEFAULT FALSE"), # Получен ли джекпот
            ("streak_days", "INTEGER DEFAULT 0"), # Серия дней подряд
            ("last_active_date", "TEXT DEFAULT ''") # Дата последней активности
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
        print("📡 [СИСТЕМА] База Supabase готова: новые модули Академии загружены.")
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
        # Пыль добавляется И в общий стаж (xp), И в кошелек (spendable_dust)
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

# === НОВЫЕ ФУНКЦИИ ДЛЯ АКАДЕМИИ ===

def get_user_data(user_id):
    """Получает полные данные пилота (для магазина и джекпота)"""
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
    """Отмечает, что джекпот сорван (чтобы не дать второй раз)"""
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
    """Списывает пыль ИЗ КОШЕЛЬКА (общий опыт XP не теряется!)"""
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
    """Проверяет, заходил ли пилот вчера. Возвращает текущую серию дней."""
    conn = get_connection()
    if not conn: return 0
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        cursor = conn.cursor()
        cursor.execute('SELECT last_active_date, streak_days FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        
        if not res:
            return 0
            
        last_date, streak = res
        
        if last_date == current_date:
            return streak # Сегодня уже давали фото, стрик не меняем
            
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        if last_date == yesterday:
            new_streak = streak + 1 # Молодец, не пропустил день!
        else:
            new_streak = 1 # Пропустил день, серия прервалась :(
            
        cursor.execute('UPDATE users SET last_active_date = %s, streak_days = %s WHERE user_id = %s', (current_date, new_streak, user_id))
        conn.commit()
        return new_streak
    finally:
        cursor.close()
        conn.close()

def get_top_pilots(limit=5):
    """Радар: Возвращает топ пилотов по опыту"""
    conn = get_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT username, xp FROM users ORDER BY xp DESC LIMIT %s', (limit,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

# === СТАРЫЕ ФУНКЦИИ ЛОГА И РАНГОВ ===
def update_personal_log(user_id, new_info):
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
