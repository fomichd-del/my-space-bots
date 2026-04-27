import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os, json, random
from PIL import Image

ANCHOR_STARS = {
    "andromeda": "Alpheratz", "aquarius": "Sadalmelik", "aquila": "Altair", "aries": "Hamal",
    "auriga": "Capella", "bootes": "Arcturus", "canis_major": "Sirius", "canis_minor": "Procyon",
    "capricornus": "Deneb Algedi", "cassiopeia": "Schedar", "cepheus": "Alderamin", "cygnus": "Deneb",
    "draco": "Thuban", "gemini": "Pollux", "hercules": "Rasalgethi", "leo": "Regulus",
    "lyra": "Vega", "orion": "Betelgeuse", "pegasus": "Markab", "perseus": "Mirfak",
    "sagittarius": "Nunki", "scorpius": "Antares", "taurus": "Aldebaran", "ursa_major": "Dubhe",
    "ursa_minor": "Polaris", "virgo": "Spica"
}

CONSTELLATION_LINES = {
    "ursa_major": [("Dubhe", "Merak"), ("Merak", "Phecda"), ("Phecda", "Megrez"), ("Megrez", "Dubhe"), ("Megrez", "Alioth"), ("Alioth", "Mizar"), ("Mizar", "Alkaid")],
    "ursa_minor": [("Polaris", "Kochab"), ("Kochab", "Pherkad"), ("Pherkad", "Zeta Ursae Minoris"), ("Zeta Ursae Minoris", "Polaris")],
    "orion": [("Betelgeuse", "Bellatrix"), ("Bellatrix", "Rigel"), ("Rigel", "Saiph"), ("Saiph", "Betelgeuse"), ("Alnitak", "Alnilam"), ("Alnilam", "Mintaka")],
    "cassiopeia": [("Segin", "Ruchbah"), ("Ruchbah", "Gamma Cassiopeiae"), ("Gamma Cassiopeiae", "Schedar"), ("Schedar", "Caph")],
    "leo": [("Regulus", "Algieba"), ("Algieba", "Adhafera"), ("Adhafera", "Rasalas"), ("Regulus", "Denebola"), ("Denebola", "Zosma"), ("Zosma", "Algieba")],
    "cygnus": [("Deneb", "Sadr"), ("Sadr", "Albireo"), ("Sadr", "Gienah"), ("Sadr", "Delta Cygni")],
    "canis_minor": [("Procyon", "Gomeisa")],
    "lyra": [("Vega", "Sheliak"), ("Sheliak", "Sulafat"), ("Sulafat", "Delta2 Lyrae"), ("Delta2 Lyrae", "Vega")]
}

def get_moon_phase(obs):
    m = ephem.Moon(obs)
    p = m.phase / 100
    if p < 0.05: return "Новолуние"
    elif p < 0.45: return f"Растущая ({int(p*100)}%)"
    elif p < 0.55: return "1-я четверть"
    elif p < 0.95: return f"Растущая ({int(p*100)}%)"
    return "Полнолуние"

def draw_constellation(ax, obs, lines, color, lw, alpha, name):
    coords = []
    for s1_n, s2_n in lines:
        try:
            s1, s2 = ephem.star(s1_n), ephem.star(s2_n)
            s1.compute(obs); s2.compute(obs)
            if s1.alt > 0 and s2.alt > 0:
                ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=alpha, zorder=3)
                coords.append((s1.az, np.pi/2 - s1.alt))
        except: pass
    if coords and name:
        avg_az = np.mean([c[0] for c in coords])
        avg_alt = np.mean([c[1] for c in coords])
        ax.text(avg_az, avg_alt, name, color=color, fontsize=10, fontweight='bold', ha='center', alpha=alpha+0.2, zorder=5)

def generate_star_map(lat, lon, user_name):
    try:
        obs = ephem.Observer(); obs.lat, obs.lon = str(lat), str(lon); obs.date = datetime.utcnow()
        with open('constellations.json', 'r', encoding='utf-8') as f: db = json.load(f)
        
        visible = [k for k, v in ANCHOR_STARS.items() if ephem.star(v).compute(obs) or True]
        target_key = random.choice(visible) if visible else "ursa_major"

        bg_img = Image.open('background1.png')
        dpi = 100; fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none'); ax.set_theta_zero_location('N'); ax.set_theta_direction(-1); ax.axis('off')

        # Звезды
        np.random.seed(int(float(lat)*100))
        ax.scatter(np.random.uniform(0, 2*np.pi, 2000), np.random.uniform(0, np.pi/2, 2000), s=np.random.uniform(0.3, 1.8), c='white', alpha=0.3)

        # Созвездия
        for cid, lines in CONSTELLATION_LINES.items():
            is_t = (cid == target_key)
            name = db[cid]['name'].split('(')[0].strip().upper() if cid in db else ""
            draw_constellation(ax, obs, lines, '#FF3366' if is_t else '#FFD700', 4 if is_t else 1.5, 0.9 if is_t else 0.4, name)

        # Солнце и Луна
        sun = ephem.Sun(); sun.compute(obs)
        if sun.alt > -0.2:
            ax.scatter(sun.az, np.pi/2 - sun.alt, s=500, c='#FFCC33', edgecolors='#FF6600', alpha=0.8, zorder=7)
            ax.text(sun.az, np.pi/2 - sun.alt + 0.15, "СОЛНЦЕ", color='#FFCC33', fontsize=12, fontweight='bold', ha='center')

        moon = ephem.Moon(); moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=400, c='#F4F6F0', alpha=0.9, zorder=7)
            ax.text(moon.az, np.pi/2 - moon.alt + 0.15, "ЛУНА", color='#F4F6F0', fontsize=12, fontweight='bold', ha='center')

        # Планеты
        for p, n, c in [(ephem.Mars(), "Марс", "#FF5733"), (ephem.Jupiter(), "Юпитер", "#4DA8DA")]:
            p.compute(obs)
            if p.alt > 0:
                ax.scatter(p.az, np.pi/2 - p.alt, s=150, c=c, edgecolors='white', zorder=6)
                ax.text(p.az, np.pi/2 - p.alt - 0.12, n, color=c, fontsize=12, fontweight='bold', ha='center')

        # Текст
        t_key = target_key if target_key in db else "ursa_major"
        target_name = db[t_key]['name'].split('(')[0].strip().upper()
        sun_cal = ephem.Sun(); sun_cal.compute(obs)
        next_rise = ephem.localtime(obs.next_rising(sun_cal)).strftime('%H:%M')
        next_set = ephem.localtime(obs.next_setting(sun_cal)).strftime('%H:%M')

        fig.text(0.38, 0.170, user_name.upper(), color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.38, 0.106, get_moon_phase(obs), color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.40, 0.067, next_rise, color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.74, 0.067, next_set, color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name, color='#D4E6FF', fontsize=22, fontweight='bold')

        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0); plt.close()
        return True, path, target_name, ""
    except Exception as e: return False, str(e), "", ""
