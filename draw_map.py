import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os, json, random
from PIL import Image

# Звезды-Якоря для выбора цели
ANCHOR_STARS = {
    "andromeda": "Alpheratz", "aquarius": "Sadalmelik", "aquila": "Altair", "aries": "Hamal",
    "auriga": "Capella", "bootes": "Arcturus", "canis_major": "Sirius", "canis_minor": "Procyon",
    "capricornus": "Deneb Algedi", "cassiopeia": "Schedar", "cepheus": "Alderamin", "cygnus": "Deneb",
    "draco": "Thuban", "gemini": "Pollux", "hercules": "Rasalgethi", "leo": "Regulus",
    "lyra": "Vega", "orion": "Betelgeuse", "pegasus": "Markab", "perseus": "Mirfak",
    "sagittarius": "Nunki", "scorpius": "Antares", "taurus": "Aldebaran", "ursa_major": "Dubhe",
    "ursa_minor": "Polaris", "virgo": "Spica"
}

# Схемы созвездий (более полные версии)
CONSTELLATION_LINES = {
    "ursa_major": [("Dubhe", "Merak"), ("Merak", "Phecda"), ("Phecda", "Megrez"), ("Megrez", "Dubhe"), ("Megrez", "Alioth"), ("Alioth", "Mizar"), ("Mizar", "Alkaid"), ("Megrez", "Phecda"), ("Phecda", "Merak")],
    "ursa_minor": [("Polaris", "Yildun"), ("Yildun", "Epsilon Ursae Minoris"), ("Epsilon Ursae Minoris", "Zeta Ursae Minoris"), ("Zeta Ursae Minoris", "Kochab"), ("Kochab", "Pherkad"), ("Pherkad", "Zeta Ursae Minoris")],
    "orion": [("Betelgeuse", "Bellatrix"), ("Bellatrix", "Meissa"), ("Meissa", "Betelgeuse"), ("Bellatrix", "Rigel"), ("Rigel", "Saiph"), ("Saiph", "Betelgeuse"), ("Alnitak", "Alnilam"), ("Alnilam", "Mintaka")],
    "cassiopeia": [("Segin", "Ruchbah"), ("Ruchbah", "Gamma Cassiopeiae"), ("Gamma Cassiopeiae", "Schedar"), ("Schedar", "Caph")],
    "leo": [("Regulus", "Eta Leonis"), ("Eta Leonis", "Algieba"), ("Algieba", "Adhafera"), ("Adhafera", "Rasalas"), ("Rasalas", "Epsilon Leonis"), ("Regulus", "Chertan"), ("Chertan", "Denebola"), ("Denebola", "Zosma"), ("Zosma", "Chertan")],
    "cygnus": [("Deneb", "Sadr"), ("Sadr", "Albireo"), ("Sadr", "Gienah"), ("Gienah", "Zeta Cygni"), ("Sadr", "Delta Cygni")],
    "draco": [("Thuban", "Eltanin"), ("Eltanin", "Rastaban"), ("Rastaban", "Kuma"), ("Kuma", "Grumium"), ("Grumium", "Eltanin"), ("Thuban", "Edasich"), ("Edasich", "Giausar")]
}

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

def draw_line(ax, obs, s1_name, s2_name, color, lw, alpha):
    try:
        s1, s2 = ephem.star(s1_name), ephem.star(s2_name)
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
        target_key = random.choice(visible_keys) if visible_keys else "ursa_major"

        # Загрузка фона
        bg_img = Image.open('background1.png')
        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.imshow(bg_img); ax_bg.axis('off')

        # Небо (Центральный круг)
        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none'); ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
        ax.grid(True, color='#4A90E2', alpha=0.1, linestyle=':'); ax.axis('off')

        # Звездный фон (пыль)
        np.random.seed(int(float(lat)*100))
        ax.scatter(np.random.uniform(0, 2*np.pi, 2000), np.random.uniform(0, np.pi/2, 2000), s=np.random.uniform(0.2, 1.5), c='white', alpha=0.3, zorder=1)

        # Отрисовка созвездий
        for cid, lines in CONSTELLATION_LINES.items():
            is_target = (cid == target_key)
            l_color = '#FF3366' if is_target else '#FFD700'
            l_width = 4.0 if is_target else 1.2
            l_alpha = 0.9 if is_target else 0.3
            for s1, s2 in lines:
                draw_line(ax, obs, s1, s2, l_color, l_width, l_alpha)

        # СОЛНЦЕ И ЛУНА (Маяки)
        sun = ephem.Sun(); sun.compute(obs)
        if sun.alt > -0.2: # Если солнце еще подсвечивает горизонт
            ax.scatter(sun.az, np.pi/2 - sun.alt, s=500, c='#FFCC33', edgecolors='#FF6600', alpha=0.9, zorder=7)
            ax.text(sun.az, np.pi/2 - sun.alt + 0.18, "СОЛНЦЕ", color='#FFCC33', fontsize=12, fontweight='bold', ha='center')

        moon = ephem.Moon(); moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=350, c='#F4F6F0', edgecolors='white', alpha=0.9, zorder=7)
            ax.text(moon.az, np.pi/2 - moon.alt + 0.18, "ЛУНА", color='#F4F6F0', fontsize=12, fontweight='bold', ha='center')

        # ПЛАНЕТЫ (Крупно)
        planets_data = [(ephem.Mars(), "Марс ♂", "#FF5733"), (ephem.Jupiter(), "Юпитер ♃", "#4DA8DA"), (ephem.Venus(), "Венера ♀", "#E2B13C")]
        for p, name, p_color in planets_data:
            p.compute(obs)
            if p.alt > 0:
                ax.scatter(p.az, np.pi/2 - p.alt, s=120, c=p_color, edgecolors='white', zorder=6)
                ax.text(p.az, np.pi/2 - p.alt - 0.12, name, color=p_color, fontsize=11, fontweight='bold', ha='center')

        # ЦЕЛЬ (Метка на карте)
        anchor_name = ANCHOR_STARS[target_key]
        s_target = ephem.star(anchor_name)
        s_target.compute(obs)
        if s_target.alt > 0:
            ax.scatter(s_target.az, np.pi/2 - s_target.alt, s=180, c='#FF3366', edgecolors='white', zorder=10)
            ax.text(s_target.az, np.pi/2 - s_target.alt + 0.12, "[ЦЕЛЬ]", color='#FF3366', fontweight='bold', fontsize=10, ha='center')

        # ТЕКСТ В РАМКАХ (Твоя калибровка)
        target_name = db[target_key]['name'].split('(')[0].strip().upper()
        
        sun_cal = ephem.Sun(); sun_cal.compute(obs)
        next_rise = ephem.localtime(obs.next_rising(sun_cal)).strftime('%H:%M')
        next_set = ephem.localtime(obs.next_setting(sun_cal)).strftime('%H:%M')

        t_color, f_size = '#D4E6FF', 22

        fig.text(0.38, 0.170, user_name.upper(), color=t_color, fontsize=f_size, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_color, fontsize=f_size, fontweight='bold')
        fig.text(0.38, 0.106, get_moon_phase(obs), color=t_color, fontsize=f_size, fontweight='bold')
        fig.text(0.40, 0.067, next_rise, color=t_color, fontsize=f_size, fontweight='bold')
        fig.text(0.74, 0.067, next_set, color=t_color, fontsize=f_size, fontweight='bold')
        fig.text(0.38, 0.028, target_name, color=t_color, fontsize=f_size, fontweight='bold')

        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        return True, path, target_name, ""
    except Exception as e:
        return False, str(e), "", ""
