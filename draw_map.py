import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os

def get_moon_phase(obs):
    try:
        m = ephem.Moon(obs)
        p = m.phase / 100
        if p < 0.05: return "🌑 Новолуние"
        elif p < 0.45: return "🌙 Растущий серп"
        elif p < 0.55: return "🌓 Первая четверть"
        elif p < 0.95: return "🌔 Растущая Луна"
        else: return "🌕 Полнолуние"
    except:
        return "🌗 Расчет фазы..."

def generate_star_map(lat, lon, user_name="Навигатор"):
    try:
        # Настройка обсерватории
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = datetime.utcnow()

        # Создаем вертикальный холст
        fig = plt.figure(figsize=(10, 16), facecolor='#010515')
        ax = fig.add_axes([0.1, 0.35, 0.8, 0.6], projection='polar')
        ax.set_facecolor('#010515')

        # 1. Рисуем глубокий космос (процедурная генерация звездной пыли)
        # Привязываем узор к координатам, чтобы у каждого города было свое небо
        np.random.seed(int(float(lat) * 100)) 
        fx = np.random.uniform(0, 2*np.pi, 4000)
        fy = np.random.uniform(0, np.pi/2, 4000)
        sizes = np.random.uniform(0.1, 2.5, 4000)
        alphas = np.random.uniform(0.1, 0.8, 4000)
        ax.scatter(fx, fy, s=sizes, c='white', alpha=alphas, edgecolors='none')

        # 2. Рисуем главные навигационные звезды
        bright_stars = ['Sirius', 'Canopus', 'Arcturus', 'Vega', 'Capella', 'Rigel', 'Procyon', 'Betelgeuse', 'Altair', 'Aldebaran', 'Spica', 'Antares']
        for name in bright_stars:
            try:
                s = ephem.star(name)
                s.compute(obs)
                if s.alt > 0: # Если звезда над горизонтом
                    ax.scatter(s.az, np.pi/2 - s.alt, s=40, c='#FFFACD', alpha=0.9)
                    ax.text(s.az, np.pi/2 - s.alt, f" {name}", color='white', fontsize=8, alpha=0.6)
            except:
                continue

        # 3. Рисуем Луну
        moon = ephem.Moon()
        moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=300, c='#F4F6F0', alpha=0.9)
            ax.text(moon.az, np.pi/2 - moon.alt, ' ЛУНА', color='#F4F6F0', fontsize=12, fontweight='bold')

        # 4. Стороны света
        for az, label in zip([0, np.pi/2, np.pi, 3*np.pi/2], ['С', 'В', 'Ю', 'З']):
            ax.text(az, 1.62, label, color='white', fontsize=20, fontweight='bold', ha='center')

        # Убираем рамки и сетку
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_axis_off()

        # 5. Золотая инфо-панель
        info = (
            f"МАРТИ АСТРОНОМ: ТВОЁ НЕБО\n"
            f"───────────────────────────\n\n"
            f"👤 ПИЛОТ: {user_name.upper()}\n"
            f"📍 КООРДИНАТЫ: {float(lat):.2f}N, {float(lon):.2f}E\n"
            f"🌗 ЛУНА: {get_moon_phase(obs)}\n\n"
            f"🎯 ЦЕЛЬ: ГЛУБОКИЙ КОСМОС"
        )
        fig.text(0.12, 0.12, info, color='#FFD700', fontsize=18, family='monospace', linespacing=1.9, va='bottom')

        # Сохранение файла
        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', facecolor='#010515', dpi=120)
        plt.close(fig)

        return True, path
    except Exception as e:
        return False, f"Ошибка отрисовки: {str(e)}"
