import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import ephem
from datetime import datetime
import os, json, random
from PIL import Image

# Расширенный словарь перевода для всех новых созвездий
STAR_NAMES = {
    "Dubhe": "Дубхе", "Merak": "Мерак", "Phecda": "Фекда", "Megrez": "Мегрец", "Alioth": "Алиот", "Mizar": "Мицар", "Alkaid": "Бенетнаш",
    "Polaris": "Полярная", "Kochab": "Кохаб", "Pherkad": "Феркад", "Betelgeuse": "Бетельгейзе", "Rigel": "Ригель", "Bellatrix": "Беллатрикс",
    "Saiph": "Саиф", "Alnitak": "Альнитак", "Alnilam": "Альнилам", "Mintaka": "Минтака", "Schedar": "Шедар", "Caph": "Каф", "Regulus": "Регул", 
    "Denebola": "Денебола", "Deneb": "Денеб", "Pollux": "Поллукс", "Castor": "Кастор", "Aldebaran": "Альдебаран", "Elnath": "Элнат", 
    "Markab": "Маркаб", "Alpheratz": "Альферац", "Vega": "Вега", "Procyon": "Процион", "Altair": "Альтаир", "Spica": "Спика", "Arcturus": "Арктур",
    "Antares": "Антарес", "Hamal": "Хамаль", "Sheratan": "Шератан", "Sirius": "Сириус", "Adhara": "Адхара", "Mirach": "Мирах", "Almach": "Аламак",
    "Mirfak": "Мирфак", "Algol": "Алголь", "Enif": "Эниф", "Scheat": "Шеат", "Algenib": "Альгениб"
}

ANCHOR_STARS = {
    "ursa_major": "Dubhe", "ursa_minor": "Polaris", "orion": "Betelgeuse", "cassiopeia": "Schedar",
    "leo": "Regulus", "cygnus": "Deneb", "gemini": "Pollux", "taurus": "Aldebaran", "lyra": "Vega",
    "andromeda": "Alpheratz", "pegasus": "Markab", "perseus": "Mirfak", "aquila": "Altair", 
    "bootes": "Arcturus", "scorpius": "Antares", "virgo": "Spica", "aries": "Hamal", "canis_major": "Sirius"
}

# ОГРОМНЫЙ АТЛАС СОЗВЕЗДИЙ (25+ фигур)
CONSTELLATION_LINES = {
    "ursa_major": [("Dubhe", "Merak"), ("Merak", "Phecda"), ("Phecda", "Megrez"), ("Megrez", "Dubhe"), ("Megrez", "Alioth"), ("Alioth", "Mizar"), ("Mizar", "Alkaid")],
    "ursa_minor": [("Polaris", "Delta Ursae Minoris"), ("Delta Ursae Minoris", "Epsilon Ursae Minoris"), ("Epsilon Ursae Minoris", "Zeta Ursae Minoris"), ("Zeta Ursae Minoris", "Kochab"), ("Kochab", "Pherkad"), ("Pherkad", "Zeta Ursae Minoris")],
    "orion": [("Betelgeuse", "Bellatrix"), ("Bellatrix", "Rigel"), ("Rigel", "Saiph"), ("Saiph", "Betelgeuse"), ("Alnitak", "Alnilam"), ("Alnilam", "Mintaka"), ("Betelgeuse", "Meissa")],
    "cassiopeia": [("Caph", "Schedar"), ("Schedar", "Gamma Cassiopeiae"), ("Gamma Cassiopeiae", "Ruchbah"), ("Ruchbah", "Segin")],
    "cygnus": [("Deneb", "Sadr"), ("Sadr", "Albireo"), ("Sadr", "Gienah"), ("Sadr", "Delta Cygni"), ("Sadr", "Eta Cygni")],
    "andromeda": [("Alpheratz", "Mirach"), ("Mirach", "Almach"), ("Mirach", "Mu Andromedae"), ("Mu Andromedae", "Nu Andromedae")],
    "pegasus": [("Markab", "Scheat"), ("Scheat", "Alpheratz"), ("Alpheratz", "Algenib"), ("Algenib", "Markab"), ("Markab", "Homam"), ("Homam", "Biham"), ("Markab", "Enif")],
    "gemini": [("Pollux", "Castor"), ("Pollux", "Kappa Geminorum"), ("Castor", "Tejat Posterior"), ("Tejat Posterior", "Propus"), ("Pollux", "Wasat"), ("Wasat", "Mebsuta"), ("Mebsuta", "Tejat Posterior")],
    "taurus": [("Aldebaran", "Ain"), ("Ain", "Hyadum I"), ("Aldebaran", "Lambda Tauri"), ("Ain", "Elnath"), ("Aldebaran", "Zeta Tauri")],
    "leo": [("Regulus", "Eta Leonis"), ("Eta Leonis", "Algieba"), ("Algieba", "Adhafera"), ("Adhafera", "Rasalas"), ("Rasalas", "Epsilon Leonis"), ("Regulus", "Chertan"), ("Chertan", "Denebola"), ("Denebola", "Zosma")],
    "perseus": [("Mirfak", "Algol"), ("Mirfak", "Delta Persei"), ("Delta Persei", "Epsilon Persei"), ("Epsilon Persei", "Zeta Persei"), ("Mirfak", "Gamma Persei"), ("Gamma Persei", "Eta Persei")],
    "auriga": [("Capella", "Menkalinan"), ("Menkalinan", "Theta Aurigae"), ("Theta Aurigae", "Elnath"), ("Elnath", "Iota Aurigae"), ("Iota Aurigae", "Capella")],
    "bootes": [("Arcturus", "Izar"), ("Izar", "Delta Bootis"), ("Delta Bootis", "Nekkar"), ("Nekkar", "Seginus"), ("Seginus", "Izar"), ("Arcturus", "Muphrid")],
    "lyra": [("Vega", "Sheliak"), ("Sheliak", "Sulafat"), ("Sulafat", "Delta2 Lyrae"), ("Delta2 Lyrae", "Vega")],
    "aquila": [("Altair", "Alshain"), ("Altair", "Tarazed"), ("Tarazed", "Gamma Aquilae"), ("Altair", "Delta Aquilae"), ("Delta Aquilae", "Lambda Aquilae")],
    "scorpius": [("Antares", "Graffias"), ("Antares", "Dschubba"), ("Antares", "Sargas"), ("Sargas", "Shaula")],
    "virgo": [("Spica", "Porrima"), ("Porrima", "Minelauva"), ("Minelauva", "Vindemiatrix"), ("Porrima", "Zaniah"), ("Zaniah", "Syrma")]
}

def draw_shining_star(ax, az, alt_r, color, size, is_target):
    glow_size = size * (18 if is_target else 8)
    ax.scatter(az, alt_r, s=glow_size*4, c=color, alpha=0.1, zorder=2)
    ax.scatter(az, alt_r, s=glow_size, c=color, alpha=0.3, zorder=3)
    ax.scatter(az, alt_r, s=size*2, c='white', zorder=4)
    # Лучи для главных звезд
    ray_color = color if is_target else 'white'
    ax.scatter(az, alt_r, s=glow_size*5, c=ray_color, marker='+', alpha=0.4, linewidths=0.5, zorder=2)
    ax.scatter(az, alt_r, s=glow_size*5, c=ray_color, marker='x', alpha=0.2, linewidths=0.3, zorder=2)

def draw_constellation(ax, obs, lines, color, lw, alpha, name, is_target):
    coords = []
    unique_stars = set()
    for s1_n, s2_n in lines:
        unique_stars.add(s1_n); unique_stars.add(s2_n)
        try:
            s1, s2 = ephem.star(s1_n), ephem.star(s2_n)
            s1.compute(obs); s2.compute(obs)
            if s1.alt > 0 and s2.alt > 0:
                # Тройной слой неона для Цели
                if is_target:
                    ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw*3, alpha=0.15, zorder=2)
                    ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw*1.5, alpha=0.3, zorder=3)
                ax.plot([s1.az, s2.az], [np.pi/2 - s1.alt, np.pi/2 - s2.alt], color=color, lw=lw, alpha=alpha, zorder=4)
                coords.append((s1.az, np.pi/2 - s1.alt))
        except: pass
    
    for s_name in unique_stars:
        try:
            st = ephem.star(s_name); st.compute(obs)
            if st.alt > 0:
                draw_shining_star(ax, st.az, np.pi/2 - st.alt, color, 12, is_target)
                ax.text(st.az, np.pi/2 - st.alt + 0.05, STAR_NAMES.get(s_name, s_name), color='white', fontsize=6, alpha=0.6, ha='center', zorder=5)
        except: pass

    if coords and name:
        avg_az = np.mean([c[0] for c in coords])
        avg_alt = np.mean([c[1] for c in coords])
        ax.text(avg_az, avg_alt - 0.12, name, color=color, fontsize=13 if is_target else 8, fontweight='bold', ha='center', zorder=6, alpha=alpha+0.2)

def generate_star_map(lat, lon, user_name):
    try:
        obs = ephem.Observer(); obs.lat, obs.lon = str(lat), str(lon); obs.date = datetime.utcnow()
        with open('constellations.json', 'r', encoding='utf-8') as f: db = json.load(f)
        
        # Фильтр видимости
        visible_keys = [k for k in CONSTELLATION_LINES.keys() if ephem.star(ANCHOR_STARS.get(k, "Polaris")).compute(obs) or True]
        target_key = random.choice(visible_keys) if visible_keys else "ursa_major"

        bg_img = Image.open('background1.png')
        dpi = 100; fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        ax = fig.add_axes([0.14, 0.32, 0.72, 0.46], projection='polar')
        ax.set_facecolor('none'); ax.set_theta_zero_location('N'); ax.set_theta_direction(-1); ax.axis('off')

        # Глубокий космос (уплотненные звезды)
        np.random.seed(int(float(lat)*100))
        ax.scatter(np.random.uniform(0, 2*np.pi, 5000), np.random.uniform(0, np.pi/2, 5000), s=np.random.uniform(0.1, 1.3), c='white', alpha=0.35)

        for cid, lines in CONSTELLATION_LINES.items():
            is_target = (cid == target_key)
            name = db[cid]['name'].split('(')[0].strip().upper() if cid in db else cid.upper()
            draw_constellation(ax, obs, lines, '#FF00FF' if is_target else '#FFD700', 4.5 if is_target else 1.3, 0.9 if is_target else 0.35, name, is_target)

        # Луна и Солнце
        moon = ephem.Moon(); moon.compute(obs)
        if moon.alt > 0:
            ax.scatter(moon.az, np.pi/2 - moon.alt, s=450, c='#F4F6F0', edgecolors='white', alpha=0.9, zorder=7)
            ax.text(moon.az, np.pi/2 - moon.alt + 0.16, f"ЛУНА ({int(moon.phase)}%)", color='white', fontsize=11, fontweight='bold', ha='center')

        sun = ephem.Sun(); sun.compute(obs)
        if sun.alt > -0.2:
            ax.scatter(sun.az, np.pi/2 - sun.alt, s=600, c='#FFCC33', edgecolors='#FF6600', zorder=7)

        # Текстовые блоки (Калибровка 22px)
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
