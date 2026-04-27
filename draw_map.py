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

# Звезды-Якоря для выбора цели
ANCHOR_STARS = {
    "andromeda": "Alpheratz", "aquarius": "Sadalmelik", "aquila": "Altair",
    "aries": "Hamal", "auriga": "Capella", "bootes": "Arcturus",
    "canis_major": "Sirius", "canis_minor": "Procyon", "capricornus": "Deneb Algedi",
    "cassiopeia": "Schedar", "cepheus": "Alderamin", "cygnus": "Deneb",
    "draco": "Thuban", "gemini": "Pollux", "hercules": "Rasalgethi",
    "leo": "Regulus", "lyra": "Vega", "orion": "Betelgeuse",
    "pegasus": "Markab", "perseus": "Mirfak", "sagittarius": "Nunki",
    "scorpius": "Antares", "taurus": "Aldebaran", "ursa_major": "Dubhe",
    "ursa_minor": "Polaris", "virgo": "Spica"
}

# Схемы созвездий (соединяем звезды линиями)
CONSTELLATION_LINES = {
    "ursa_major": [("Dubhe", "Merak"), ("Merak", "Phecda"), ("Phecda", "Megrez"), ("Megrez", "Dubhe"), ("Megrez", "Alioth"), ("Alioth", "Mizar"), ("Mizar", "Alkaid")],
    "ursa_minor": [("Polaris", "Kochab"), ("Kochab", "Pherkad"), ("Pherkad", "Delta Ursae Minoris"), ("Delta Ursae Minoris", "Polaris")],
    "orion": [("Betelgeuse", "Bellatrix"), ("Bellatrix", "Rigel"), ("Rigel", "Saiph"), ("Saiph", "Betelgeuse"), ("Alnitak", "Alnilam"), ("Alnilam", "Mintaka")],
    "cassiopeia": [("Segin", "Ruchbah"), ("Ruchbah", "Gamma Cassiopeiae"), ("Gamma Cassiopeiae", "Schedar"), ("Schedar", "Caph")],
    "leo": [("Regulus", "Algieba"), ("Algieba", "Adhafera"), ("Adhafera", "Rasalas"), ("Regulus", "Denebola"), ("Denebola", "Zosma"), ("Zosma", "Algieba")],
    "cygnus": [("Deneb", "Sadr"), ("Sadr", "Albireo"), ("Sadr", "Gienah"), ("Sadr", "Delta Cygni")],
    "gemini": [("Pollux", "Castor"), ("Pollux", "Alhena"), ("Castor", "Mebsuta")],
    "taurus": [("Aldebaran", "Elnath"), ("Aldebaran", "Zeta Tauri")],
    "pegasus": [("Markab", "Scheat"), ("Scheat", "Alpheratz"), ("Alpheratz", "Algenib"), ("Algenib", "Markab")],
    "andromeda": [("Alpheratz", "Mirach"), ("Mirach", "Almach")],
    "bootes": [("Arcturus", "Izar"), ("Izar", "Seginus"), ("Seginus", "Nekkar"), ("Nekkar", "Arcturus")],
    "aquila": [("Altair", "Alshain"), ("Altair", "Tarazed")],
    "lyra": [("Vega", "Sheliak"), ("Sheliak", "Sulafat"), ("Sulafat", "Delta2 Lyrae"), ("Delta2 Lyrae", "Vega")],
    "scorpius": [("Antares", "Graffias"), ("Antares", "Shaula"), ("Antares", "Dschubba")],
    "virgo": [("Spica", "Porrima"), ("Porrima", "Auva"), ("Auva", "Vindemiatrix")],
    "draco": [("Thuban", "Eltanin"), ("Eltanin", "Rastaban"), ("Rastaban", "Altais")]
}

# Словарь для хранения вычисленных центров созвездий
CONSTELLATION_CENTERS = {}

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

def calculate_constellation_center(obs, lines):
    unique_stars = set()
    for s1, s2 in lines:
        unique_stars.add(s1)
        unique_stars.add(s2)
    
    visible_stars_az = []
    visible_stars_alt_r = []
    for star_name in unique_stars:
        try:
            s = ephem.star(star_name)
            s.compute(obs)
            if s.alt > 0:
                visible_stars_az.append(s.az)
                visible_stars_alt_r.append(np.pi/2 - s.alt)
        except: pass
    
    if not visible_stars_az: return None, None
    
    mean_az = np.mean(visible_stars_az)
    mean_alt_r = np.mean(visible_stars_alt_r)
    return mean_az, mean_alt_r

def draw_line(ax, obs, star1, star2, color='white', lw=1, alpha=0.4):
    try:
        s1, s2 = ephem.star(star1), ephem.star(star2)
        s1.compute(obs); s2.compute(obs)
        if s1.alt > 0 and s2.alt > 0:
            ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=alpha, zorder=3)
    except: pass

def generate_star_map(lat, lon, user_name):
    try:
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = datetime.utcnow()

        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        # Выбор цели
        visible_keys = []
        for key, anchor in ANCHOR_STARS.items():
            if key in db:
                try:
                    s = ephem.star(anchor)
                    s.compute(obs)
                    if s.alt > 0: visible_keys.append(key)
                except: pass
        target_key = random.choice(visible_keys) if visible_keys else None

        bg_img = Image.open('background1.png')
        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.imshow(bg_img)
        ax_bg.axis('off')

        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none')
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.grid(True, color='#4A90E2', alpha=0.15, linestyle=':')
        ax.set_yticklabels([]); ax.set_xticklabels([])
        ax.spines['polar'].set_visible(False)

        # Звездный фон
        np.random.seed(int(float(lat)*100))
        fx = np.random.uniform(0, 2*np.pi, 2500)
        fy = np.random.uniform(0, np.pi/2, 2500)
        ax.scatter(fx, fy, s=np.random.uniform(0.3, 2), c='#D4E6FF', alpha=0.4, zorder=1)

        # --- ОТРИСОВКА ЛИНИЙ И НАЗВАНИЙ СОЗВЕЗДИЙ ---
        # Сначала очистим словарь центров
        CONSTELLATION_CENTERS.clear()
        
        for const_id, lines in CONSTELLATION_LINES.items():
            is_target = (const_id == target_key)
            l_color = '#FF3366' if is_target else '#FFD700'
            l_alpha = 1.0 if is_target else 0.5  # Было 0.2
            l_width = 5.0 if is_target else 1.5  # Было 0.8
            for s1, s2 in lines:
                draw_line(ax, obs, s1, s2, color=l_color, lw=l_width, alpha=l_alpha)
            
            # Добавляем названия для ВСЕХ
            n_color = '#FF3366' if is_target else 'white'
            n_alpha = 1.0 if is_target else 0.6
            n_size = 14 if is_target else 10
            n_weight = 'bold' if is_target else 'normal'
            const_name = db[const_id]['name'].split('(')[0].strip().upper() # Из JSON

            # Находим центр созвездия
            center_az, center_alt_r = calculate_constellation_center(obs, lines)
            if center_az is not None:
                # Отрисовываем название в центре созвездия
                ax.text(center_az, center_alt_r, const_name, color=n_color, fontsize=n_size, fontweight=n_weight, alpha=n_alpha, ha='center', zorder=4)

        # Планеты (Крупно)
        planets_data = [(ephem.Mars(), "Марс ♂", "#FF5733"), (ephem.Jupiter(), "Юпитер ♃", "#4DA8DA"), (ephem.Venus(), "Венера ♀", "#E2B13C"), (ephem.Saturn(), "Сатурн ♄", "#C5B358")]
        for p, name, p_color in planets_data:
            p.compute(obs)
            if p.alt > 0:
                ax.scatter(p.az, np.pi/2 - p.alt, s=120, c=p_color, edgecolors='white', linewidth=0.5, zorder=6) # Было s=45
                ax.text(p.az, np.pi/2 - p.alt - 0.12, name, color=p_color, fontsize=14, fontweight='bold', ha='center', zorder=7) # Было fontsize=8

        # Подписи ярких звезд (Крупнее)
        for eng_name, rus_name in BRIGHT_STARS:
            try:
                s = ephem.star(eng_name)
                s.compute(obs)
                if s.alt > 5:
                    ax.scatter(s.az, np.pi/2 - s.alt, s=30, c='white', alpha=0.9, zorder=4) # Было s=12
                    ax.text(s.az, np.pi/2 - s.alt + 0.08, rus_name, color='white', fontsize=10, alpha=0.7, ha='center', zorder=5) # Было fontsize=7
            except: pass

        # Луна
        moon = ephem.Moon(); moon.compute(obs)
        phase_str = get_moon_phase(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=200, c='#F4F6F0', alpha=0.9, zorder=8)

        # Финализация цели (Убрали старый текст)
        target_name, target_fact = "ГЛУБОКИЙ КОСМОС", "Космос полон тайн!"
        if target_key:
            anchor_name = ANCHOR_STARS[target_key]
            s = ephem.star(anchor_name)
            s.compute(obs)
            # Эффект прицела на якоре цели
            ax.scatter(s.az, np.pi/2 - s.alt, s=250, c='#FF3366', edgecolors='white', zorder=10) # Было s=150
            # Название созвездия-цели уже жирно и крупно отрисовано в центре созвездия.
            
            target_name = db[target_key]['name'].split('(')[0].strip().upper()
            target_fact = f"{db[target_key]['description']}\n{db[target_key]['secret']}"

        # Калибровка текста (Твои рамки не трогал)
        sun = ephem.Sun()
        next_rise = ephem.localtime(obs.next_rising(sun)).strftime('%H:%M')
        next_set = ephem.localtime(obs.next_setting(sun)).strftime('%H:%M')
        t_color, f_size = '#D4E6FF', 22

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
