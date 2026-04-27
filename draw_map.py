import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os, json, random
from PIL import Image

# Расширенный перевод ярчайших звезд
STAR_NAMES = {
    "Dubhe": "Дубхе", "Merak": "Мерак", "Phecda": "Фекда", "Megrez": "Мегрец", "Alioth": "Алиот", "Mizar": "Мицар", "Alkaid": "Бенетнаш",
    "Polaris": "Полярная", "Kochab": "Кохаб", "Pherkad": "Феркад", "Betelgeuse": "Бетельгейзе", "Rigel": "Ригель", "Bellatrix": "Беллатрикс",
    "Alnitak": "Альнитак", "Alnilam": "Альнилам", "Mintaka": "Минтака", "Schedar": "Шедар", "Caph": "Каф", "Regulus": "Регул", 
    "Denebola": "Денебола", "Deneb": "Денеб", "Pollux": "Поллукс", "Castor": "Кастор", "Aldebaran": "Альдебаран", "Elnath": "Элнат", 
    "Markab": "Маркаб", "Alpheratz": "Альферац", "Vega": "Вега", "Procyon": "Процион", "Altair": "Альтаир", "Spica": "Спика", "Arcturus": "Арктур",
    "Sirius": "Сириус", "Antares": "Антарес", "Hamal": "Хамаль", "Sheratan": "Шератан", "Capella": "Капелла", "Canopus": "Канопус", "Mirfak": "Мирфак"
}

ANCHOR_STARS = {
    "ursa_major": "Dubhe", "ursa_minor": "Polaris", "orion": "Betelgeuse", "cassiopeia": "Schedar",
    "leo": "Regulus", "cygnus": "Deneb", "gemini": "Pollux", "taurus": "Aldebaran", "lyra": "Vega",
    "aries": "Hamal", "scorpius": "Antares", "virgo": "Spica", "aquila": "Altair", "bootes": "Arcturus",
    "pegasus": "Markab", "auriga": "Capella", "andromeda": "Alpheratz"
}

# ПОЛНЫЙ ЗОДИАКАЛЬНЫЙ И ГРАНД-АТЛАС (Все созвездия прорисованы полностью)
CONSTELLATION_LINES = {
    "ursa_major": [("Dubhe", "Merak"), ("Merak", "Phecda"), ("Phecda", "Megrez"), ("Megrez", "Dubhe"), ("Megrez", "Alioth"), ("Alioth", "Mizar"), ("Mizar", "Alkaid")],
    "ursa_minor": [("Polaris", "Yildun"), ("Yildun", "Epsilon Ursae Minoris"), ("Epsilon Ursae Minoris", "Zeta Ursae Minoris"), ("Zeta Ursae Minoris", "Kochab"), ("Kochab", "Pherkad"), ("Pherkad", "Zeta Ursae Minoris")],
    "orion": [("Betelgeuse", "Bellatrix"), ("Bellatrix", "Rigel"), ("Rigel", "Saiph"), ("Saiph", "Betelgeuse"), ("Alnitak", "Alnilam"), ("Alnilam", "Mintaka"), ("Betelgeuse", "Meissa")],
    "cassiopeia": [("Caph", "Schedar"), ("Schedar", "Gamma Cassiopeiae"), ("Gamma Cassiopeiae", "Ruchbah"), ("Ruchbah", "Segin")],
    "leo": [("Regulus", "Eta Leonis"), ("Eta Leonis", "Algieba"), ("Algieba", "Adhafera"), ("Adhafera", "Rasalas"), ("Rasalas", "Epsilon Leonis"), ("Regulus", "Chertan"), ("Chertan", "Denebola"), ("Denebola", "Zosma")],
    "cygnus": [("Deneb", "Sadr"), ("Sadr", "Albireo"), ("Sadr", "Gienah"), ("Gienah", "Epsilon Cygni"), ("Epsilon Cygni", "Zeta Cygni"), ("Sadr", "Delta Cygni"), ("Delta Cygni", "Theta Cygni")],
    "gemini": [("Pollux", "Castor"), ("Pollux", "Wasat"), ("Wasat", "Mebsuta"), ("Mebsuta", "Tejat Posterior"), ("Castor", "Mebsuta"), ("Pollux", "Alhena"), ("Alhena", "Alzirr")],
    "taurus": [("Aldebaran", "Ain"), ("Ain", "Hyadum I"), ("Aldebaran", "Lambda Tauri"), ("Ain", "Elnath"), ("Aldebaran", "Zeta Tauri")],
    "aries": [("Hamal", "Sheratan"), ("Sheratan", "Mesarthim"), ("Mesarthim", "41 Arietis")],
    "scorpius": [("Antares", "Graffias"), ("Antares", "Dschubba"), ("Antares", "Sargas"), ("Sargas", "Shaula"), ("Shaula", "Lesath")],
    "virgo": [("Spica", "Porrima"), ("Porrima", "Minelauva"), ("Minelauva", "Vindemiatrix"), ("Porrima", "Zaniah"), ("Zaniah", "Syrma"), ("Syrma", "Khambalia")],
    "aquarius": [("Sadalmelik", "Sadalsuud"), ("Sadalsuud", "Sadachbia"), ("Sadachbia", "Eta Aquarii"), ("Eta Aquarii", "Sadalmelik"), ("Sadachbia", "Zeta Aquarii"), ("Zeta Aquarii", "Pi Aquarii")],
    "sagittarius": [("Kaus Media", "Kaus Australis"), ("Kaus Australis", "Ascella"), ("Ascella", "Nunki"), ("Nunki", "Kaus Borealis"), ("Kaus Borealis", "Kaus Media"), ("Kaus Media", "Alnasl")],
    "libra": [("Zubeneschamali", "Zubenelgenubi"), ("Zubenelgenubi", "Brachium"), ("Brachium", "Zubeneschamali")],
    "cancer": [("Acubens", "Asellus Australis"), ("Asellus Australis", "Asellus Borealis"), ("Asellus Borealis", "Tegmine")],
    "capricornus": [("Algedi", "Dabih"), ("Dabih", "Nashira"), ("Nashira", "Deneb Algedi"), ("Deneb Algedi", "Algedi")]
}

def draw_shining_star(ax, az, alt_r, color, size, is_target):
    glow_size = size * (30 if is_target else 15)
    ax.scatter(az, alt_r, s=glow_size*5, c=color, alpha=0.1, zorder=2)
    ax.scatter(az, alt_r, s=glow_size, c=color, alpha=0.3, zorder=3)
    ax.scatter(az, alt_r, s=size*4, c='white', zorder=4)
    # Сияющие лучи (дифракция)
    ray_col = color if is_target else 'white'
    ax.scatter(az, alt_r, s=glow_size*8, c=ray_col, marker='+', alpha=0.4, linewidths=1.5, zorder=2)

def draw_constellation(ax, obs, lines, color, lw, alpha, name, is_target):
    coords = []
    unique_stars = set()
    for s1_n, s2_n in lines:
        unique_stars.add(s1_n); unique_stars.add(s2_n)
        try:
            s1, s2 = ephem.star(s1_n), ephem.star(s2_n)
            s1.compute(obs); s2.compute(obs)
            if s1.alt > 0 and s2.alt > 0:
                ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=alpha, zorder=3)
                ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw*4, alpha=alpha*0.2, zorder=2)
                coords.append((s1.az, np.pi/2 - s1.alt))
        except: pass
    
    for s_name in unique_stars:
        try:
            st = ephem.star(s_name); st.compute(obs)
            if st.alt > 0:
                draw_shining_star(ax, st.az, np.pi/2 - st.alt, color, 14, is_target)
                # ОГРОМНЫЕ НАЗВАНИЯ ЗВЕЗД
                ax.text(st.az, np.pi/2 - st.alt + 0.07, STAR_NAMES.get(s_name, s_name), color='white', fontsize=14, alpha=0.8, ha='center', zorder=5)
        except: pass

    if coords and name:
        avg_az = np.mean([c[0] for c in coords]); avg_alt = np.mean([c[1] for c in coords])
        # ГИГАНТСКИЕ НАЗВАНИЯ СОЗВЕЗДИЙ
        ax.text(avg_az, avg_alt - 0.25, name, color=color, fontsize=24 if is_target else 18, fontweight='bold', ha='center', zorder=6, bbox=dict(facecolor='black', alpha=0.5, edgecolor='none'))

def generate_star_map(lat, lon, user_name):
    try:
        obs = ephem.Observer(); obs.lat, obs.lon = str(lat), str(lon); obs.date = datetime.utcnow()
        with open('constellations.json', 'r', encoding='utf-8') as f: db = json.load(f)
        
        visible_keys = [k for k in CONSTELLATION_LINES.keys() if ephem.star(ANCHOR_STARS.get(k, "Polaris")).compute(obs) or True]
        target_key = random.choice(visible_keys) if visible_keys else "ursa_major"

        bg_img = Image.open('background1.png')
        dpi = 100; fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none'); ax.set_theta_zero_location('N'); ax.set_theta_direction(-1); ax.axis('off')

        # ГЛУБОКОЕ НЕБО (8000 звезд)
        np.random.seed(int(float(lat)*100))
        ax.scatter(np.random.uniform(0, 2*np.pi, 8000), np.random.uniform(0, np.pi/2, 8000), s=np.random.uniform(0.1, 2.5), c='white', alpha=0.4)

        for cid, lines in CONSTELLATION_LINES.items():
            is_target = (cid == target_key)
            name = db[cid]['name'].split('(')[0].strip().upper() if cid in db else cid.upper()
            draw_constellation(ax, obs, lines, '#FF00FF' if is_target else '#FFD700', 7.0 if is_target else 3.0, 0.9 if is_target else 0.4, name, is_target)

        # ЛУНА И СОЛНЦЕ (ГИГАНТЫ)
        moon = ephem.Moon(); moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=700, c='#F4F6F0', alpha=0.9, zorder=8)
            ax.text(moon.az, np.pi/2 - moon.alt + 0.2, f"ЛУНА ({int(moon.phase)}%)", color='white', fontsize=16, fontweight='bold', ha='center')

        sun = ephem.Sun(); sun.compute(obs)
        if sun.alt > -0.6:
            ax.scatter(sun.az, np.pi/2 - sun.alt, s=1000, c='#FFCC33', edgecolors='#FF6600', zorder=8)
            ax.text(sun.az, np.pi/2 - sun.alt + 0.25, "СОЛНЦЕ", color='#FFCC33', fontsize=24, fontweight='bold', ha='center')

        # ПЛАНЕТЫ (МАКСИМУМ)
        for p, sym, n, c in [(ephem.Mars(), "♂", "МАРС", "#FF4500"), (ephem.Jupiter(), "♃", "ЮПИТЕР", "#4DA8DA"), (ephem.Saturn(), "♄", "САТУРН", "#C5B358")]:
            p.compute(obs)
            if p.alt > 0:
                ax.scatter(p.az, np.pi/2 - p.alt, s=400, c=c, edgecolors='white', zorder=7)
                ax.text(p.az, np.pi/2 - p.alt - 0.25, f"{sym} {n}", color=c, fontsize=20, fontweight='bold', ha='center')

        # ТЕКСТ (22px КАЛИБРОВКА)
        t_key = target_key if target_key in db else "ursa_major"
        target_name = db[t_key]['name'].split('(')[0].strip().upper()
        rise = ephem.localtime(obs.next_rising(ephem.Sun())).strftime('%H:%M')
        sset = ephem.localtime(obs.next_setting(ephem.Sun())).strftime('%H:%M')

        fig.text(0.38, 0.170, user_name.upper(), color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.38, 0.106, f"Фаза: {int(moon.phase)}%", color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.40, 0.067, rise, color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.74, 0.067, sset, color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name, color='#FF00FF', fontsize=22, fontweight='bold')

        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0, facecolor='#0B0D14')
        plt.close(); return True, path, target_name, ""
    except Exception as e: return False, str(e), "", ""
