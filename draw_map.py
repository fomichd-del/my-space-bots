import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os
from PIL import Image

def get_moon_phase(obs):
    try:
        m = ephem.Moon(obs)
        p = m.phase / 100
        if p < 0.05: return "Новолуние"
        elif p < 0.45: return f"Растущая ({int(p*100)}%)"
        elif p < 0.55: return "Первая четверть"
        elif p < 0.95: return f"Растущая ({int(p*100)}%)"
        else: return "Полнолуние"
    except:
        return "Расчет..."

def draw_line(ax, obs, star1, star2, color='white', lw=1.5):
    try:
        s1, s2 = ephem.star(star1), ephem.star(star2)
        s1.compute(obs); s2.compute(obs)
        if s1.alt > 0 and s2.alt > 0:
            ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=0.8)
    except: pass

def generate_star_map(lat, lon, user_name="Навигатор"):
    try:
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = datetime.utcnow()

        # 1. Загружаем фон
        try:
            bg_img = Image.open('background1.png')
        except FileNotFoundError:
            return False, "⚠️ Файл background1.png не найден на сервере!"

        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)

        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.imshow(bg_img)
        ax_bg.axis('off')

        # 2. КАРТА НЕБА
        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none')
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.axis('off')

        # --- ЗВЕЗДЫ ---
        np.random.seed(int(float(lat) * 100))
        fx = np.random.uniform(0, 2*np.pi, 3000)
        fy = np.random.uniform(0, np.pi/2, 3000)
        sizes = np.random.uniform(0.5, 3.0, 3000)
        ax.scatter(fx, fy, s=sizes, c='#D4E6FF', alpha=0.8, edgecolors='none')

        # --- СОЗВЕЗДИЯ И ЛИНИИ ---
        c_color = '#FFD700'
        uma = ['Alkaid', 'Mizar', 'Alioth', 'Megrez', 'Phecda', 'Merak', 'Dubhe']
        for i in range(len(uma)-1): draw_line(ax, obs, uma[i], uma[i+1], color=c_color)
        cas = ['Segin', 'Ruchbah', 'Gamma Cassiopeiae', 'Schedar', 'Caph']
        for i in range(len(cas)-1): draw_line(ax, obs, cas[i], cas[i+1], color=c_color)
        
        o_color = '#4DA8DA'
        draw_line(ax, obs, 'Betelgeuse', 'Bellatrix', color=o_color)
        draw_line(ax, obs, 'Bellatrix', 'Rigel', color=o_color)
        draw_line(ax, obs, 'Rigel', 'Saiph', color=o_color)
        draw_line(ax, obs, 'Saiph', 'Betelgeuse', color=o_color)
        draw_line(ax, obs, 'Alnitak', 'Alnilam', color='white', lw=2)
        draw_line(ax, obs, 'Alnilam', 'Mintaka', color='white', lw=2)

        labels = [('Dubhe', 'Б. Медведица', c_color), ('Schedar', 'Кассиопея', c_color), 
                  ('Betelgeuse', 'Орион', 'white'), ('Vega', 'Вега', '#A5B4D9')]
        for star, name, color in labels:
            try:
                s = ephem.star(star)
                s.compute(obs)
                if s.alt > 0:
                    ax.scatter(s.az, np.pi/2 - s.alt, s=60, c=color)
                    ax.text(s.az, np.pi/2 - s.alt + 0.08, f" {name}", color=color, fontsize=12, fontweight='bold')
            except: pass

        planets = [(ephem.Mars(), 'Марс ♂', '#FF5733'), (ephem.Jupiter(), 'Юпитер ♃', '#4DA8DA')]
        for p, name, color in planets:
            p.compute(obs)
            if p.alt > 0:
                ax.scatter(p.az, np.pi/2 - p.alt, s=120, c=color)
                ax.text(p.az, np.pi/2 - p.alt + 0.08, name, color=color, fontsize=12, fontweight='bold')

        moon = ephem.Moon()
        moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=350, c='#F4F6F0', alpha=0.9)

        # 3. ВПЕЧАТЫВАЕМ ТЕКСТ (Ювелирная калибровка)
        sun = ephem.Sun()
        next_rise = ephem.localtime(obs.next_rising(sun)).strftime('%H:%M')
        next_set = ephem.localtime(obs.next_setting(sun)).strftime('%H:%M')

        t_color = '#D4E6FF'
        f_size = 22 

        # ПИЛОТ: подняли выше
        fig.text(0.38, 0.182, user_name.upper(), color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        
        # КООРДИНАТЫ: подняли выше и сдвинули правее
        fig.text(0.48, 0.153, f"{float(lat):.2f}°N, {float(lon):.2f}°E", color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        
        # ЛУНА: подняли
        fig.text(0.38, 0.124, get_moon_phase(obs), color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        
        # ВОСХОД / ЗАКАТ: опустили ниже и сдвинули правее
        fig.text(0.40, 0.075, next_rise, color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.70, 0.075, next_set, color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        
        # ЦЕЛЬ: опустили сильно ниже
        fig.text(0.38, 0.042, "ГЛУБОКИЙ КОСМОС", color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')

        # Сохранение
        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)

        return True, path
    except Exception as e:
        return False, f"Ошибка отрисовки: {str(e)}"
