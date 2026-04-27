import numpy as np
import ephem
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import os

def get_moon_phase(obs):
    try:
        m = ephem.Moon(obs)
        p = m.phase / 100
        if p < 0.05: return "New Moon"
        elif p < 0.45: return "Waxing Crescent"
        elif p < 0.55: return "First Quarter"
        elif p < 0.95: return "Waxing Gibbous"
        else: return "Full Moon"
    except:
        return "Waxing Luna"

def generate_star_map(lat, lon, user_name="Navigator"):
    try:
        # Настройка обсерватории
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = datetime.utcnow()

        # Создаем вертикальный холст (9:16)
        fig = plt.figure(figsize=(10, 16), facecolor='#010515')
        
        # Карта (верхняя часть)
        ax = fig.add_axes([0.1, 0.35, 0.8, 0.6], projection='polar')
        ax.set_facecolor('#010515')

        # 1. ЯРКИЙ фон глубокого космоса (узор привязан к координатам)
        np.random.seed(int(float(lat) * 100)) 
        fx = np.random.uniform(0, 2*np.pi, 6000)
        fy = np.random.uniform(0, np.pi/2, 6000)
        sizes = np.random.uniform(0.1, 3.0, 6000)
        ax.scatter(fx, fy, s=sizes, c='white', alpha=0.9, edgecolors='none')

        # 2. Рисуем созвездие ОРИОН (БЕЗ ТЕКСТА)
        stars = ['Sirius', 'Rigel', 'Betelgeuse', 'Alnitak', 'Alnilam', 'Mintaka', 'Bellatrix', 'Saiph']
        points = {}
        for s_name in stars:
            try:
                s = ephem.star(s_name)
                s.compute(obs)
                if s.alt > 0:
                    ax.scatter(s.az, np.pi/2 - s.alt, s=50, c='#FFFACD', alpha=0.95)
                    points[s_name] = (s.az, np.pi/2 - s.alt)
                    if s_name in ['Sirius', 'Rigel', 'Betelgeuse']:
                         ax.text(s.az, np.pi/2 - s.alt, f" {s_name}", color='white', fontsize=9, alpha=0.6)
            except: pass

        # Линии пояса Ориона
        belt = ['Alnitak', 'Alnilam', 'Mintaka']
        belt_points = [points[s] for s in belt if s in points]
        if len(belt_points) > 1:
            bz, br = zip(*belt_points)
            ax.plot(bz, br, c='gold', lw=1, alpha=0.3)

        # 3. Рисуем ЛУНУ (Она яркая и большая)
        moon = ephem.Moon()
        moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=400, c='#F4F6F0', alpha=0.9)
            ax.text(moon.az, np.pi/2 - moon.alt, ' MOON', color='#F4F6F0', fontsize=12, fontweight='bold')

        # 4. Стороны света (используем стандартные буквы)
        for az, label in zip([0, np.pi/2, np.pi, 3*np.pi/2], ['N', 'E', 'S', 'W']):
            ax.text(az, 1.65, label, color='white', fontsize=22, fontweight='bold', ha='center')

        # Убираем рамки
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_axis_off()

        # 5. Золотая инфо-панель (русский текст без сложных шрифтов)
        sun = ephem.Sun()
        info = (
            f"МАРТИ АСТРОНОМ: ТВОЁ НЕБО\n"
            f"───────────────────────────\n\n"
            f"👤 ПИЛОТ: {user_name[:15].upper()}\n"
            f"📍 КООРДИНАТЫ: {float(lat):.2f}N, {float(lon):.2f}E\n"
            f"🌗 ЛУНА: {get_moon_phase(obs)}\n\n"
            f"🎯 ЦЕЛЬ: СОЗВЕЗДИЕ ОРИОН"
        )
        # fig.text — это самый надежный метод для Render
        plt.figtext(0.12, 0.12, info, color='#FFD700', fontsize=18, 
                    family='monospace', linespacing=2, va='bottom')

        # Сохранение файла
        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', facecolor='#010515', dpi=120)
        plt.close(fig)

        return True, path
    except Exception as e:
        return False, f"Ошибка отрисовки: {str(e)}"
