import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os, json, random
from PIL import Image

# Звезды-Якоря (Цели)
ANCHOR_STARS = {
    "andromeda": "Alpheratz", "aquarius": "Sadalmelik", "aquila": "Altair", "aries": "Hamal",
    "auriga": "Capella", "bootes": "Arcturus", "canis_major": "Sirius", "canis_minor": "Procyon",
    "capricornus": "Deneb Algedi", "cassiopeia": "Schedar", "cepheus": "Alderamin", "cygnus": "Deneb",
    "draco": "Thuban", "gemini": "Pollux", "hercules": "Rasalgethi", "leo": "Regulus",
    "lyra": "Vega", "orion": "Betelgeuse", "pegasus": "Markab", "perseus": "Mirfak",
    "sagittarius": "Nunki", "scorpius": "Antares", "taurus": "Aldebaran", "ursa_major": "Dubhe",
    "ursa_minor": "Polaris", "virgo": "Spica"
}

# МАСШТАБНЫЙ АТЛАС ЛИНИЙ
CONSTELLATION_LINES = {
    "ursa_major": [("Dubhe", "Merak"), ("Merak", "Phecda"), ("Phecda", "Megrez"), ("Megrez", "Dubhe"), ("Megrez", "Alioth"), ("Alioth", "Mizar"), ("Mizar", "Alkaid")],
    "ursa_minor": [("Polaris", "Kochab"), ("Kochab", "Pherkad"), ("Pherkad", "Zeta Ursae Minoris"), ("Zeta Ursae Minoris", "Polaris")],
    "orion": [("Betelgeuse", "Bellatrix"), ("Bellatrix", "Rigel"), ("Rigel", "Saiph"), ("Saiph", "Betelgeuse"), ("Alnitak", "Alnilam"), ("Alnilam", "Mintaka")],
    "cassiopeia": [("Segin", "Ruchbah"), ("Ruchbah", "Gamma Cassiopeiae"), ("Gamma Cassiopeiae", "Schedar"), ("Schedar", "Caph")],
    "leo": [("Regulus", "Algieba"), ("Algieba", "Adhafera"), ("Adhafera", "Rasalas"), ("Regulus", "Denebola"), ("Denebola", "Zosma"), ("Zosma", "Algieba")],
    "cygnus": [("Deneb", "Sadr"), ("Sadr", "Albireo"), ("Sadr", "Gienah"), ("Sadr", "Delta Cygni")],
    "gemini": [("Pollux", "Castor"), ("Pollux", "Alhena"), ("Castor", "Mebsuta")],
    "taurus": [("Aldebaran", "Elnath"), ("Aldebaran", "Zeta Tauri")],
    "pegasus": [("Markab", "Scheat"), ("Scheat", "Alpheratz"), ("Alpheratz", "Algenib"), ("Algenib", "Markab")],
    "lyra": [("Vega", "Sheliak"), ("Sheliak", "Sulafat"), ("Sulafat", "Delta2 Lyrae"), ("Delta2 Lyrae", "Vega")],
    "aquila": [("Altair", "Alshain"), ("Altair", "Tarazed")],
    "bootes": [("Arcturus", "Izar"), ("Izar", "Seginus"), ("Seginus", "Nekkar"), ("Nekkar", "Arcturus")]
}

def get_moon_phase_info(obs):
    m = ephem.Moon(obs)
    p = int(m.phase)
    if p < 5: return "Новолуние", p
    elif p < 45: return "Растущая", p
    elif p < 55: return "1-я Четверть", p
    elif p < 95: return "Растущая", p
    return "Полнолуние", p

def draw_glow_star(ax, az, alt_r, size, color):
    # Рисуем звезду в 3 слоя для эффекта свечения
    ax.scatter(az, alt_r, s=size*10, c=color, alpha=0.1, edgecolors='none', zorder=2)
    ax.scatter(az, alt_r, s=size*4, c=color, alpha=0.3, edgecolors='none', zorder=2)
    ax.scatter(az, alt_r, s=size, c='white', edgecolors='none', zorder=3)

def generate_star_map(lat, lon, user_name):
    try:
        obs = ephem.Observer(); obs.lat, obs.lon = str(lat), str(lon); obs.date = datetime.utcnow()
        with open('constellations.json', 'r', encoding='utf-8') as f: db = json.load(f)
        
        visible = [k for k, v in ANCHOR_STARS.items() if ephem.star(v).compute(obs) or True]
        target_key = random.choice(visible) if visible else "ursa_major"

        bg_img = Image.open('background1.png')
        dpi = 100; fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi, facecolor='#0B0D14')
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none'); ax.set_theta_zero_location('N'); ax.set_theta_direction(-1); ax.axis('off')

        # 1. Звезды (Glow effect)
        np.random.seed(int(float(lat)*100))
        for _ in range(800):
            az, alt_r = np.random.uniform(0, 2*np.pi), np.random.uniform(0, np.pi/2)
            ax.scatter(az, alt_r, s=np.random.uniform(0.5, 4), c='white', alpha=0.4, zorder=1)

        # 2. Созвездия (Линии и Названия)
        for cid, lines in CONSTELLATION_LINES.items():
            is_t = (cid == target_key)
            color = '#00FFFF' if is_t else '#FFD700'
            alpha = 1.0 if is_t else 0.4
            lw = 3.5 if is_t else 1.2
            
            coords = []
            for s1_n, s2_n in lines:
                try:
                    s1, s2 = ephem.star(s1_n), ephem.star(s2_n)
                    s1.compute(obs); s2.compute(obs)
                    if s1.alt > 0 and s2.alt > 0:
                        ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=alpha, zorder=3)
                        coords.append((s1.az, np.pi/2 - s1.alt))
                except: pass
            
            if coords and cid in db:
                name = db[cid]['name'].split('(')[0].strip().upper()
                avg_az = np.mean([c[0] for c in coords])
                avg_alt = np.mean([c[1] for c in coords])
                ax.text(avg_az, avg_alt, name, color=color, fontsize=11 if is_t else 8, fontweight='bold', ha='center', alpha=alpha+0.2, zorder=5)

        # 3. Планеты (Символы как в референсе)
        planets = [
            (ephem.Mars(), "♂ МАРС", "#FF4500"),
            (ephem.Jupiter(), "♃ ЮПИТЕР", "#4DA8DA"),
            (ephem.Venus(), "♀ ВЕНЕРА", "#FFD700"),
            (ephem.Saturn(), "♄ САТУРН", "#C5B358")
        ]
        legend_labels = []
        for p, name, p_col in planets:
            p.compute(obs)
            if p.alt > 0:
                ax.scatter(p.az, np.pi/2 - p.alt, s=150, c=p_col, edgecolors='white', linewidth=1.5, zorder=6)
                ax.text(p.az, np.pi/2 - p.alt - 0.1, name, color=p_col, fontsize=11, fontweight='bold', ha='center')
                legend_labels.append(f"{name}")

        # 4. Солнце и Луна
        moon = ephem.Moon(); moon.compute(obs)
        m_phase_txt, m_pct = get_moon_phase_info(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=500, c='#F4F6F0', alpha=0.9, edgecolors='white', zorder=7)
            ax.text(moon.az, np.pi/2 - moon.alt + 0.18, f"ЛУНА {m_pct}%", color='white', fontsize=10, fontweight='bold', ha='center')

        # 5. Текст в рамках (Твоя калибровка сохранена)
        t_key = target_key if target_key in db else "ursa_major"
        target_name = db[t_key]['name'].split('(')[0].strip().upper()
        sun = ephem.Sun(); sun.compute(obs)
        rise = ephem.localtime(obs.next_rising(sun)).strftime('%H:%M')
        sset = ephem.localtime(obs.next_setting(sun)).strftime('%H:%M')

        fig.text(0.38, 0.170, user_name.upper(), color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.38, 0.106, f"{m_phase_txt} ({m_pct}%)", color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.40, 0.067, rise, color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.74, 0.067, sset, color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name, color='#00FFFF', fontsize=22, fontweight='bold')

        # 6. Легенда планет внизу круга
        if legend_labels:
            fig.text(0.5, 0.28, "ЛЕГЕНДА ПЛАНЕТ: " + " | ".join(legend_labels), color='white', fontsize=10, ha='center', alpha=0.7)

        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0, facecolor='#0B0D14')
        plt.close(); return True, path, target_name, ""
    except Exception as e: return False, str(e), "", ""
