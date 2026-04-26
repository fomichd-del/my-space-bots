import numpy as np
import ephem
import matplotlib.pyplot as plt
from datetime import datetime
import os

def get_moon_phase(observer):
    moon = ephem.Moon(observer)
    phase = moon.phase / 100  # Процент освещенности
    if phase < 0.05: return "🌑 Новолуние"
    elif phase < 0.45: return "🌙 Растущий серп"
    elif phase < 0.55: return "🌓 Первая четверть"
    elif phase < 0.95: return "🌔 Растущая Луна"
    else: return "🌕 Полнолуние"

def generate_star_map(lat, lon, user_name="Навигатор"):
    observer = ephem.Observer()
    observer.lat, observer.lon = str(lat), str(lon)
    observer.date = datetime.utcnow()
    
    # 1. Создаем вертикальный холст (9:16)
    fig = plt.figure(figsize=(10, 16), facecolor='#010515')
    
    # Верхняя часть: Карта неба (Полярная проекция)
    ax = fig.add_axes([0.1, 0.4, 0.8, 0.5], projection='polar')
    ax.set_facecolor('#010515')
    
    # Рисуем градиент неба и Млечный Путь (пыль)
    faint_x = np.random.uniform(0, 2*np.pi, 15000)
    faint_y = np.random.uniform(0, np.pi/2, 15000)
    ax.scatter(faint_x, faint_y, s=0.05, c='white', alpha=0.1)

    # Рисуем звезды
    for (mag, name, db) in ephem.stars._stars:
        s = ephem.star(name)
        s.compute(observer)
        if s.alt > 0 and s.mag < 4.5:
            size = (5 - s.mag) ** 2.5
            color = 'white' if s.mag > 1.5 else '#FFFACD' # Самые яркие чуть желтоватые
            ax.scatter(s.az, np.pi/2 - s.alt, s=size, c=color, alpha=0.8, edgecolors='none')
            if s.mag < 1.2:
                ax.text(s.az, np.pi/2 - s.alt, s.name, color='white', fontsize=7, alpha=0.5)

    # Навигация (С Ю В З)
    for az, label in zip([0, np.pi/2, np.pi, 3*np.pi/2], ['С', 'В', 'Ю', 'З']):
        ax.text(az, 1.6, label, color='white', fontsize=18, fontweight='bold', ha='center')

    # 2. Информационная панель (нижняя часть)
    info_ax = fig.add_axes([0.1, 0.05, 0.8, 0.3])
    info_ax.axis('off')
    
    moon_text = get_moon_phase(observer)
    sun = ephem.Sun()
    next_rise = observer.next_rising(sun)
    next_set = observer.next_setting(sun)

    info_content = (
        f"МАРТИ АСТРОНОМ: ТВОЁ НЕБО\n"
        f"___________________________\n\n"
        f"👤 ПИЛОТ: {user_name.upper()}\n"
        f"📍 КООРДИНАТЫ: {lat:.2f}, {lon:.2f}\n"
        f"🌗 ФАЗА ЛУНЫ: {moon_text}\n"
        f"🌅 ВОСХОД: {ephem.localtime(next_rise).strftime('%H:%M')}\n"
        f"🌇 ЗАКАТ: {ephem.localtime(next_set).strftime('%H:%M')}\n\n"
        f"🎯 ЦЕЛЬ ДНЯ: ОРИОН (Ищи в южной части неба)"
    )

    info_ax.text(0, 0.5, info_content, color='#FFD700', fontsize=14, linespacing=2, family='monospace')

    # Очистка осей карты
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.grid(False)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.spines['polar'].set_visible(False)

    filename = f"sky_map_{datetime.now().strftime('%H%M%S')}.png"
    plt.savefig(filename, bbox_inches='tight', facecolor='#010515', dpi=150)
    plt.close()
    return filename
