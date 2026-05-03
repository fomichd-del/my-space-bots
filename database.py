import sqlite3

def init_db():
    """Создает таблицу пользователей, если она еще не существует"""
    conn = sqlite3.connect('marty_space.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            xp INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_xp(user_id, amount, username="Пилот"):
    """Начисляет опыт пользователю"""
    conn = sqlite3.connect('marty_space.db')
    cursor = conn.cursor()
    # Если пользователя нет в базе — добавляем, если есть — обновляем XP
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    cursor.execute('UPDATE users SET xp = xp + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    """Возвращает текущий XP пользователя"""
    conn = sqlite3.connect('marty_space.db')
    cursor = conn.cursor()
    cursor.execute('SELECT xp FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def get_rank_name(xp):
    """Определяет звание на основе накопленного опыта"""
    if xp < 50: return "Кадет-наблюдатель 🐣"
    if xp < 150: return "Пилот-исследователь 🚀"
    if xp < 300: return "Старший штурман 🧭"
    if xp < 500: return "Командор орбиты 👨‍🚀"
    return "Адмирал Галактики 👑"
