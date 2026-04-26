import numpy as np
import ephem
import matplotlib
matplotlib.use('Agg') # КРИТИЧЕСКИ ВАЖНО ДЛЯ RENDER
import matplotlib.pyplot as plt
from datetime import datetime
import os

def get_moon_phase(observer):
    try:
        moon = ephem.Moon(observer)
        phase = moon.phase / 100
        if phase < 0.05: return "🌑 Новолуние"
        elif phase < 0.45: return "🌙 Растущий серп"
        elif phase < 0.55: return "🌓 Первая четверть"
        elif phase < 0.95: return "🌔 Растущая Луна"
        else: return "🌕 Полнолуние"
    except: return "🌗 Фаза уточняется"

def generate_star_map(lat, lon, user_name="Навигатор"):
    observer = ephem.Observer()
    observer.lat, observer.lon = str(lat), str(lon)
    observer.date = datetime.utcnow()
    
    # 1. Создаем вертикальный холст (9:16)
    fig = plt.figure(figsize=(10, 16), facecolor='#010515')
    
    # Карта неба
    ax = fig.add_axes([0.1, 0.4, 0.8, 0.5], projection='polar')
    ax.set_facecolor('#010515')
    
    # Млечный путь (пыль)
    faint_x = np.random.uniform(0, 2*np.pi, 10000)
    faint_y = np.random.uniform(0, np.pi/2, 10000)
    ax.scatter(faint_x, faint_y, s=0.1, c='white', alpha=0.1)

    # Звезды
    for (mag, name, db) in ephem.stars._stars:
        try:
            s = ephem.star(name)
            s.compute(observer)
            if s.alt > 0 and s.mag < 4.5:
                size = (5 - s.mag) ** 2.5
                ax.scatter(s.az, np.pi/2 - s.alt, s=size, c='white', alpha=0.8)
                if s.mag < 1.5:
                    ax.text(s.az, np.pi/2 - s.alt, s.name, color='white', fontsize=8, alpha=0.6)
        except: continue

    # Навигация
    for az, label in zip([0, np.pi/2, np.pi, 3*np.pi/2], ['С', 'В', 'Ю', 'З']):
        ax.text(az, 1.6, label, color='white', fontsize=18, fontweight='bold', ha='center')

    # Инфо-панель
    info_ax = fig.add_axes([0.1, 0.05, 0.8, 0.3])
    info_ax.axis('off')
    
    sun = ephem.Sun()
    next_rise = observer.next_rising(sun)
    next_set = observer.next_setting(sun)

    info_content = (
        f"МАРТИ АСТРОНОМ: ТВОЁ НЕБО\n"
        f"___________________________\n\n"
        f"👤 ПИЛОТ: {user_name.upper()}\n"
        f"📍 КООРДИНАТЫ: {lat:.2f}N, {lon:.2f}E\n"
        f"🌗 ЛУНА: {get_moon_phase(observer)}\n"
        f"🌅 ВОСХОД: {ephem.localtime(next_rise).strftime('%H:%M')}\n"
        f"🌇 ЗАКАТ: {ephem.localtime(next_set).strftime('%H:%M')}\n\n"
        f"🎯 ЦЕЛЬ: ОРИОН (Золотое созвездие)"
    )
    info_ax.text(0, 0.5, info_content, color='#FFD700', fontsize=16, family='monospace')

    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.grid(False)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.spines['polar'].set_visible(False)

    filename = f"sky_map_{datetime.now().strftime('%H%M%S')}.png"
    plt.savefig(filename, bbox_inches='tight', facecolor='#010515', dpi=120)
    plt.close(fig)
    return filename
