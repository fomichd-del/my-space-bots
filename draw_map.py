import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os
import json
import random
from PIL import Image

# Звезды-Якоря для наведения прицела
ANCHOR_STARS = {
    "andromeda": "Alpheratz", "aquarius": "Sadalmelik", "aquila": "Altair",
    "aries": "Hamal", "auriga": "Capella", "bootes": "Arcturus",
    "canes_venatici": "Cor Caroli", "canis_major": "Sirius", "canis_minor": "Procyon",
    "capricornus": "Deneb Algedi", "carina": "Canopus", "cassiopeia": "Schedar",
    "centaurus": "Rigil Kentaurus", "cepheus": "Alderamin", "cetus": "Menkar",
    "columba": "Phact", "corona_borealis": "Alphecca", "corvus": "Alchiba",
    "crater": "Alkes", "crux": "Acrux", "cygnus": "Deneb", "delphinus": "Sualocin",
    "draco": "Thuban", "eridanus": "Achernar", "gemini": "Pollux", "grus": "Alnair",
    "hercules": "Rasalgethi", "hydra": "Alphard", "leo": "Regulus", "lepus": "Arneb",
    "libra": "Zubenelgenubi", "lyra": "Vega", "ophiuchus": "Rasalhague",
    "orion": "Betelgeuse", "pavo": "Peacock", "pegasus": "Markab", "perseus": "Mirfak",
    "phoenix": "Ankaa", "pisces": "Alrescha", "piscis_austrinus": "Fomalhaut",
    "puppis": "Naos", "sagittarius": "Nunki", "scorpius": "Antares", "serpens": "Unukalhai",
    "taurus": "Aldebaran", "triangulum_australe": "Atria", "ursa_major": "Dubhe",
    "ursa_minor": "Polaris", "vela": "Suhail", "virgo": "Spica"
}

# Список ярких звезд для подписи на карте
BRIGHT_STARS = [
    ("Sirius", "Сириус"), ("Vega", "Вега"), ("Capella", "Капелла"), 
    ("Rigel", "Ригель"), ("Procyon", "Процион"), ("Betelgeuse", "Бетельгейзе"),
    ("Altair", "Альтаир"), ("Aldebaran", "Альдебаран"), ("Antares", "Антарес"),
    ("Spica", "Спика"), ("Pollux", "Поллукс"), ("Deneb", "Денеб"), ("Regulus", "Регул")
]

def get_moon_phase(obs):
    try:
        m = ephem.Moon(obs)
        p = m.phase / 100
        if p < 0.05: return "Новолуние"
        elif p < 0.45: return f"Растущая ({int(p*100)}%)"
        elif p < 0.55: return "1-я четверть"
        elif p < 0.95: return f"Растущая ({int(p*100)}%)"
        else: return "Полнолуние"
    except: return "Расчет..."

def draw_line(ax, obs, star1, star2, color='white', lw=1):
    try:
        s1, s2 = ephem.star(star1), ephem.star(star2)
        s1.compute(obs)
        if s1.alt > 0 and s2.alt > 0:
            ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=0.4)
    except: pass

def generate_star_map(lat, lon, user_name):
    try:
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = datetime.utcnow()

        # Загрузка базы
        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        # Поиск целей
        visible_keys = []
        for key, anchor in ANCHOR_STARS.items():
            if key in db:
                try:
                    s = ephem.star(anchor)
                    s.compute(obs)
                    if s.alt > 0: visible_keys.append(key)
                except: pass
        
        target_key = random.choice(visible_keys) if visible_keys else None

        # Рендеринг
        bg_img = Image.open('background1.png')
        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.imshow(bg_img)
        ax_bg.axis('off')

        # Слой неба
        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none')
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        
        # Сетка координат (паутинка)
        ax.grid(True, color='#4A90E2', alpha=0.15, linestyle=':')
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        ax.spines['polar'].set_visible(False)

        # Звездная пыль
        np.random.seed(int(float(lat)*100))
        fx = np.random.uniform(0, 2*np.pi, 2500)
        fy = np.random.uniform(0, np.pi/2, 2500)
        ax.scatter(fx, fy, s=np.random.uniform(0.3, 2), c='#D4E6FF', alpha=0.5, zorder=1)

        # Подписи ярких звезд
        for eng_name, rus_name in BRIGHT_STARS:
            try:
                s = ephem.star(eng_name)
                s.compute(obs)
                if s.alt > 10: # Только если высоко над горизонтом
                    ax.scatter(s.az, np.pi/2 - s.alt, s=15, c='white', alpha=0.8, zorder=2)
                    ax.text(s.az, np.pi/2 - s.alt + 0.04, rus_name, color='white', fontsize=7, alpha=0.6, ha='center')
            except: pass

        # Планеты
        planets_data = [
            (ephem.Mars(), "Марс ♂", "#FF5733"),
            (ephem.Jupiter(), "Юпитер ♃", "#4DA8DA"),
            (ephem.Venus(), "Венера ♀", "#E2B13C"),
            (ephem.Saturn(), "Сатурн ♄", "#C5B358")
        ]
        for p, name, p_color in planets_data:
            p.compute(obs)
            if p.alt > 0:
                ax.scatter(p.az, np.pi/2 - p.alt, s=50, c=p_color, edgecolors='white', linewidth=0.5, zorder=5)
                ax.text(p.az, np.pi/2 - p.alt - 0.06, name, color=p_color, fontsize=9, fontweight='bold', ha='center')

        # Луна
        moon = ephem.Moon()
        moon.compute(obs)
        phase_str = get_moon_phase(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=250, c='#F4F6F0', alpha=0.9, zorder=6)
            ax.text(moon.az, np.pi/2 - moon.alt + 0.12, phase_str, color='#F4F6F0', fontsize=8, ha='center', fontweight='bold')

        # Основные созвездия (линии)
        c_color = '#FFD700'
        uma = ['Alkaid', 'Mizar', 'Alioth', 'Megrez', 'Phecda', 'Merak', 'Dubhe']
        for i in range(len(uma)-1): draw_line(ax, obs, uma[i], uma[i+1], color=c_color)
        cas = ['Segin', 'Ruchbah', 'Gamma Cassiopeiae', 'Schedar', 'Caph']
        for i in range(len(cas)-1): draw_line(ax, obs, cas[i], cas[i+1], color=c_color)

        # ЦЕЛЬ (Подсветка)
        target_name = "ГЛУБОКИЙ КОСМОС"
        target_fact = "Космос полон тайн!"
        if target_key:
            anchor_name = ANCHOR_STARS[target_key]
            s = ephem.star(anchor_name)
            s.compute(obs)
            # Эффект пульсации цели
            ax.scatter(s.az, np.pi/2 - s.alt, s=180, c='#FF3366', edgecolors='white', zorder=10)
            ax.scatter(s.az, np.pi/2 - s.alt, s=600, c='#FF3366', alpha=0.2, zorder=9)
            ax.text(s.az, np.pi/2 - s.alt + 0.1, "[ ЦЕЛЬ ]", color='#FF3366', fontweight='bold', fontsize=11, ha='center')
            target_name = db[target_key]['name'].split('(')[0].strip().upper()
            target_fact = f"{db[target_key]['description']}\n{db[target_key]['history']}\n{db[target_key]['secret']}"

        # Текст (Калибровка 4.0 сохранена)
        sun = ephem.Sun()
        next_rise = ephem.localtime(obs.next_rising(sun)).strftime('%H:%M')
        next_set = ephem.localtime(obs.next_setting(sun)).strftime('%H:%M')
        t_color = '#D4E6FF'
        f_size = 22

        fig.text(0.38, 0.170, user_name.upper(), color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.38, 0.106, phase_str, color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.40, 0.067, next_rise, color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.74, 0.067, next_set, color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')
        fig.text(0.38, 0.028, target_name, color=t_color, fontsize=f_size, fontweight='bold', ha='left', va='center')

        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        return True, path, target_name, target_fact
    except Exception as e:
        return False, str(e), None, None
