import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime, timezone
import os, json, random, gc, math # Добавили math
from PIL import Image
import ephem
import warnings

# Глушим технические предупреждения
warnings.filterwarnings("ignore", category=FutureWarning)

# Расширенный список целей согласно твоему constellations.json
TARGETS = {
    "andromeda": [15, 40], "antlia": [150, -35], "apus": [240, -75], "aquarius": [345, -15],
    "aquila": [297, 3], "ara": [255, -55], "aries": [38, 20], "auriga": [90, 42],
    "bootes": [218, 28], "caelum": [70, -38], "camelopardalis": [88, 70], "cancer": [130, 20],
    "canes_venatici": [200, 38], "canis_major": [105, -20], "canis_minor": [115, 6], "capricornus": [315, -20],
    "carina": [135, -60], "cassiopeia": [15, 60], "centaurus": [200, -45], "cepheus": [335, 70],
    "cetus": [25, -10], "chamaeleon": [165, -78], "circinus": [220, -63], "columba": [90, -35],
    "coma_berenices": [192, 23], "corona_australis": [285, -40], "corona_borealis": [235, 30], "corvus": [185, -18],
    "crater": [170, -15], "crux": [185, -60], "cygnus": [310, 45], "delphinus": [308, 14],
    "dorado": [78, -55], "draco": [260, 65], "equuleus": [318, 7], "eridanus": [58, -30],
    "fornax": [40, -30], "gemini": [105, 22], "grus": [338, -45], "hercules": [255, 30],
    "horologium": [45, -52], "hydra": [150, -20], "hydrus": [35, -70], "indus": [315, -55],
    "lacerta": [338, 45], "leo": [160, 15], "leo_minor": [155, 35], "lepus": [85, -20],
    "libra": [230, -15], "lupus": [235, -40], "lynx": [120, 45], "lyra": [283, 39],
    "mensa": [85, -77], "microscopium": [315, -35], "monoceros": [105, 0], "musca": [188, -70],
    "norma": [242, -50], "octans": [0, -85], "ophiuchus": [255, -8], "orion": [85, 3],
    "pavo": [280, -65], "pegasus": [345, 20], "perseus": [55, 45], "phoenix": [10, -48],
    "pictor": [85, -53], "pisces": [0, 10], "piscis_austrinus": [340, -30], "puppis": [115, -40],
    "pyxis": [135, -30], "reticulum": [60, -60], "sagitta": [298, 18], "sagittarius": [285, -25],
    "scorpius": [250, -35], "sculptor": [0, -33], "scutum": [282, -10], "serpens": [250, 0],
    "sextans": [152, 0], "taurus": [65, 15], "telescopium": [285, -50], "triangulum": [30, 32],
    "triangulum_australe": [240, -65], "tucana": [0, -60], "ursa_major": [160, 55], "ursa_minor": [250, 88],
    "vela": [142, -50], "virgo": [200, -2], "volans": [120, -70], "vulpecula": [305, 25]
}

def generate_star_map(lat, lon, user_name, user_id):
    gc.collect() 
    temp_file = f"tmp_{user_id}.png"
    final_path = f"sky_{user_id}.jpg"
    
    try:
        # --- НАСТРОЙКА НАБЛЮДАТЕЛЯ ДЛЯ ПРОВЕРКИ ВИДИМОСТИ ---
        e_obs = ephem.Observer()
        e_obs.lat, e_obs.lon, e_obs.date = str(lat), str(lon), datetime.now()
        
        # Фильтруем созвездия: выбираем только те, что сейчас выше 10 градусов над горизонтом
        visible_targets = []
        for key, pos in TARGETS.items():
            star = ephem.FixedBody()
            star._ra = math.radians(pos[0]) 
            star._dec = math.radians(pos[1])
            star.compute(e_obs)
            if math.degrees(star.alt) > 10:
                visible_targets.append(key)
        
        # Если ничего не нашли (редко, но вдруг), берем Большую Медведицу
        target_key = random.choice(visible_targets) if visible_targets else "ursa_major"
        
        dt = datetime.now(timezone.utc)
        observer = Observer(dt=dt, lat=float(lat), lon=float(lon))
        
        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        target_pos = TARGETS[target_key]
        target_name_rus = db.get(target_key, {}).get('name', target_key).split('(')[0].strip().upper()

        style = PlotStyle().extend(extensions.BLUE_GOLD, extensions.GRADIENT_PRE_DAWN)
        try:
            style.star.label.font_size = 11
            style.constellation.label.font_size = 16
            style.constellation.label.font_weight = 700
            style.constellation.line.stroke_width = 2.5
        except: pass

        p = ZenithPlot(observer=observer, style=style, resolution=1400, autoscale=True)

        p.horizon(); p.milky_way(); p.ecliptic(); p.constellations()
        try: p.constellation_borders()
        except: pass
        p.constellation_labels() 
        try: p.dsos(where=[_.magnitude < 6.0], labels=True)
        except: pass
        p.stars(where=[_.magnitude < 6.0], where_labels=[_.magnitude < 2.5]) 
        p.planets(); p.sun(); p.moon()

        p.marker(
            ra=target_pos[0], dec=target_pos[1],
            label="[ TARGET ]",
            style={
                "marker": {"size": 80, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 3, "line_style": [1, [5, 5]]},
                "label": {"font_size": 24, "font_weight": 800, "font_color": "#FF00FF", "offset_y": 50}
            }
        )

        p.export(temp_file, transparent=True, padding=0.01)
        plt.close('all')

        moon = ephem.Moon(); moon.compute(e_obs)
        sun = ephem.Sun(); sun.compute(e_obs)
        moon_phase = int(moon.phase)
        try:
            rise_time = ephem.localtime(e_obs.next_rising(sun)).strftime('%H:%M')
            set_time = ephem.localtime(e_obs.next_setting(sun)).strftime('%H:%M')
        except: rise_time, set_time = "--:--", "--:--"

        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_file).convert("RGBA")
        sky_size = 880
        sky_img = sky_img.resize((sky_size, sky_size), Image.Resampling.LANCZOS)
        
        x_offset = (bg_img.width - sky_size) // 2
        y_offset = 360
        bg_img.paste(sky_img, (x_offset, y_offset), sky_img)
        
        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        t_col = '#D4E6FF'
        fig.text(0.38, 0.170, user_name.upper(), color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.106, f"Фаза: {moon_phase}%", color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.40, 0.067, rise_time, color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.74, 0.067, set_time, color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=22, fontweight='bold')

        plt.savefig(final_path.replace(".jpg", ".png"), bbox_inches='tight', pad_inches=0, dpi=dpi)
        plt.close('all')
        
        final_img = Image.open(final_path.replace(".jpg", ".png")).convert("RGB")
        final_img.save(final_path, "JPEG", quality=85, optimize=True)
        
        bg_img.close(); sky_img.close(); final_img.close()
        if os.path.exists(temp_file): os.remove(temp_file)
        if os.path.exists(final_path.replace(".jpg", ".png")): os.remove(final_path.replace(".jpg", ".png"))
        gc.collect()
        
        return True, final_path, target_name_rus, ""

    except Exception as e:
        plt.close('all')
        if os.path.exists(temp_file): os.remove(temp_file)
        gc.collect()
        return False, str(e), "", ""
