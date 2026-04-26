import numpy as np
import ephem
import matplotlib
matplotlib.use('Agg') # Обязательно для сервеers без монитора
import matplotlib.pyplot as plt
from datetime import datetime
import os

def get_moon_phase(obs):
    try:
        m = ephem.Moon(obs)
        p = m.phase / 100
        if p < 0.05: return "Новолуние 🌑"
        elif p < 0.45: return "Растущий серп 🌙"
        elif p < 0.55: return "Первая четверть 🌓"
        elif p < 0.95: return "Растущая Луна 🌔"
        else: return "Полнолуние 🌕"
    except: return "Уточняется 🌗"

def generate_star_map(lat, lon, user_name="Навигатор"):
    # 1. Настройка наблюдателя
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.date = datetime.utcnow()
    
    # 2. Создаем вертикальный холст (Смартфон-стайл)
    fig = plt.figure(figsize=(10, 16), facecolor='#010515')
    
    # Карта (верхняя часть)
    ax = fig.add_axes([0.1, 0.35, 0.8, 0.6], projection='polar')
    ax.set_facecolor('#010515')
    
    # Эффект Млечного пути (звездная пыль)
    fx = np.random.uniform(0, 2*np.pi, 8000)
    fy = np.random.uniform(0, np.pi/2, 8000)
    ax.scatter(fx, fy, s=0.15, c='white', alpha=0.15)

    # Рисуем звезды из базы данных
    for (mag, name, db) in ephem.stars._stars:
        try:
            s = ephem.star(name)
            s.compute(obs)
            if s.alt > 0 and s.mag < 4.2:
                # Размер звезды зависит от её яркости
                size = (5 - s.mag) ** 2.2
                ax.scatter(s.az, np.pi/2 - s.alt, s=size, c='white', alpha=0.8, edgecolors='none')
                
                # Подписываем только самые яркие
                if s.mag < 1.3:
                    ax.text(s.az, np.pi/2 - s.alt, s.name, color='white', 
                            fontsize=9, alpha=0.5, ha='left', va='bottom')
        except: continue

    # Метки сторон света
    for az, label in zip([0, np.pi/2, np.pi, 3*np.pi/2], ['С', 'В', 'Ю', 'З']):
        ax.text(az, 1.62, label, color='white', fontsize=22, fontweight='bold', ha='center')

    # 3. Золотистая инфо-панель (нижняя часть)
    sun = ephem.Sun()
    next_rise = obs.next_rising(sun)
    next_set = obs.next_setting(sun)
    
    info_text = (
        f"МАРТИ АСТРОНОМ: ТВОЁ НЕБО\n"
        f"───────────────────────────\n\n"
        f"👤 ПИЛОТ: {user_name[:15].upper()}\n"
        f"📍 ПОЗИЦИЯ: {float(lat):.2f}N, {float(lon):.2f}E\n"
        f"🌗 ЛУНА: {get_moon_phase(obs)}\n"
        f"🌅 ВОСХОД: {ephem.localtime(next_rise).strftime('%H:%M')}\n"
        f"🌇 ЗАКАТ: {ephem.localtime(next_set).strftime('%H:%M')}\n\n"
        f"🎯 ЦЕЛЬ: ОРИОН (Золотое созвездие)"
    )
    
    # Размещаем текст внизу
    fig.text(0.12, 0.12, info_text, color='#FFD700', fontsize=18, 
             family='monospace', linespacing=1.9, va='bottom')

    # Финальная чистка осей
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_axis_off()

    # Сохранение файла
    filename = f"sky_{datetime.now().strftime('%H%M%S')}.png"
    plt.savefig(filename, bbox_inches='tight', facecolor='#010515', dpi=120)
    plt.close(fig)
    return filename
