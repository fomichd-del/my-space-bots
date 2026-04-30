import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime, timezone
import os, json, random, gc, math
from PIL import Image
import ephem
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# КАТАЛОГ СОЗВЕЗДИЙ (RA, DEC)
TARGETS = {
    "andromeda": [15, 40], "antlia": [150, -35], "apus": [240, -75], "aquarius": [335, -10],
    "aquila": [297, 8], "ara": [260, -55], "aries": [35, 20], "auriga": [88, 42],
    "bootes": [218, 28], "caelum": [70, -38], "camelopardalis": [88, 70], "cancer": [130, 20],
    "canes_venatici": [200, 40], "canis_major": [103, -20], "canis_minor": [115, 5], "capricornus": [315, -20],
    "carina": [135, -60], "cassiopeia": [15, 60], "centaurus": [200, -45], "cepheus": [335, 70],
    "cetus": [30, -10], "chamaeleon": [165, -78], "circinus": [220, -63], "columba": [85, -35],
    "coma_berenices": [190, 23], "corona_australis": [285, -40], "corona_borealis": [233, 26], "corvus": [185, -18],
    "crater": [170, -15], "crux": [185, -60], "cygnus": [308, 44], "delphinus": [308, 13],
    "dorado": [75, -55], "draco": [255, 67], "equuleus": [318, 5], "eridanus": [58, -25],
    "fornax": [40, -30], "gemini": [110, 22], "grus": [335, -45], "hercules": [255, 30],
    "horologium": [45, -52], "hydra": [150, -20], "hydrus": [35, -75], "indus": [315, -55],
    "lacerta": [335, 45], "leo": [160, 15], "leo_minor": [155, 35], "lepus": [80, -20],
    "libra": [230, -15], "lupus": [235, -45], "lynx": [120, 45], "lyra": [283, 38],
    "mensa": [85, -75], "microscopium": [315, -35], "monoceros": [105, -5], "musca": [188, -70],
    "norma": [242, -50], "octans": [0, -88], "ophiuchus": [255, -8], "orion": [83, 0],
    "pavo": [300, -65], "pegasus": [345, 20], "perseus": [50, 45], "phoenix": [10, -48],
    "pictor": [85, -53], "pisces": [10, 15], "piscis_austrinus": [338, -30], "puppis": [115, -40],
    "pyxis": [135, -30], "reticulum": [60, -60], "sagitta": [298, 18], "sagittarius": [285, -25],
    "scorpius": [250, -30], "sculptor": [0, -30], "scutum": [280, -10], "serpens": [255, 0],
    "sextans": [152, 0], "taurus": [72, 16], "telescopium": [285, -52], "triangulum": [30, 32],
    "triangulum_australe": [240, -65], "tucana": [0, -60], "ursa_major": [165, 50], "ursa_minor": [250, 80],
    "vela": [140, -50], "virgo": [200, -5], "volans": [115, -70], "vulpecula": [302, 25]
}

def generate_star_map(lat, lon, user_name, user_id):
    gc.collect() 
    temp_file = f"tmp_{user_id}.png"
    final_path = f"sky_{user_id}.jpg"
    
    try:
        dt = datetime.now(timezone.utc)
        observer = Observer(dt=dt, lat=float(lat), lon=float(lon))
        
        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        e_obs = ephem.Observer()
        e_obs.lat, e_obs.lon, e_obs.date = str(lat), str(lon), datetime.now()
        
        visible_targets = []
        for key, pos in TARGETS.items():
            body = ephem.FixedBody()
            body._ra = math.radians(pos[0]); body._dec = math.radians(pos[1])
            body.compute(e_obs)
            if math.degrees(body.alt) > 10: visible_targets.append(key)

        target_key = random.choice(visible_targets) if visible_targets else "ursa_major"
        target_pos = TARGETS[target_key]
        target_name_rus = db.get(target_key, {}).get('name', target_key).split('(')[0].strip().upper()

        style = PlotStyle().extend(extensions.BLUE_GOLD, extensions.GRADIENT_PRE_DAWN)
        try:
            style.star.label.font_size = 11
            style.constellation.label.font_size = 16
            style.constellation.label.font_weight = 700
            style.constellation.line.stroke_width = 2.5
            style.constellation.line.color = "#5c9dff"
        except: pass

        # Создаем карту (Разрешение 1600 - безопасно для памяти)
        p = ZenithPlot(observer=observer, style=style, resolution=1600, autoscale=True)

        p.horizon()
        p.milky_way() 
        p.constellations()
        
        # --- [ НОВЫЕ ДЕТАЛИ ] ---
        # 1. Эклиптика (Красный пунктир)
        p.ecliptic(color="#ff4c4c", linestyle="dashed", linewidth=1.2, alpha=0.7)
        # 2. Небесный экватор (Синий пунктир)
        p.celestial_equator(color="#4c4cff", linestyle="dashed", linewidth=1.2, alpha=0.7)
        # 3. Дип-скай объекты (Те самые кружочки)
        # Ставим labels=False, чтобы были только значки без текста
        try: p.dsos(where=[_.magnitude < 5.5], labels=False)
        except: pass

        try: p.constellation_borders() 
        except: pass
        p.constellation_labels() 
        
        p.stars(where=[_.magnitude < 6.2], where_labels=[_.magnitude < 3.5]) 
        p.planets(); p.sun(); p.moon()

        # Маркер цели
        p.marker(
            ra=target_pos[0], dec=target_pos[1], label="ЦЕЛЬ!",
            style={
                "marker": {"size": 100, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 3},
                "label": {"font_size": 30, "font_weight": 900, "font_color": "#FF00FF", "offset_y": 60}
            }
        )

        p.export(temp_file, transparent=True, padding=0.01)
        plt.close('all')
        del p

        # СБОРКА ФИНАЛЬНОЙ КАРТОЧКИ
        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_file).convert("RGBA")
        
        sky_size = 940 
        sky_img = sky_img.resize((sky_size, sky_size), Image.Resampling.LANCZOS)
        
        x_offset = (bg_img.width - sky_size) // 2
        y_offset = 360 - ((sky_size - 880) // 2)
        bg_img.paste(sky_img, (x_offset, y_offset), sky_img)
        
        # Поднимаем DPI для четкости текста
        dpi = 180 
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(bg_img); ax.axis('off')

        moon = ephem.Moon(); moon.compute(e_obs)
        sun = ephem.Sun(); sun.compute(e_obs)
        moon_phase = int(moon.phase)
        try:
            rise_time = ephem.localtime(e_obs.next_rising(sun)).strftime('%H:%M')
            set_time = ephem.localtime(e_obs.next_setting(sun)).strftime('%H:%M')
        except: rise_time, set_time = "--:--", "--:--"

        t_col = '#D4E6FF'
        fig.text(0.38, 0.170, user_name.upper(), color=t_col, fontsize=16, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_col, fontsize=12, fontweight='bold')
        fig.text(0.35, 0.106, f"Фаза: {moon_phase}%", color=t_col, fontsize=12, fontweight='bold')
        fig.text(0.35, 0.067, rise_time, color=t_col, fontsize=12, fontweight='bold')
        fig.text(0.74, 0.067, set_time, color=t_col, fontsize=12, fontweight='bold')
        fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=16, fontweight='bold')

        tmp_png = f"fin_{user_id}.png"
        plt.savefig(tmp_png, bbox_inches='tight', pad_inches=0, dpi=dpi)
        plt.close(fig)
        
        with Image.open(tmp_png) as img:
            img.convert("RGB").save(final_path, "JPEG", quality=95, optimize=True)
        
        bg_img.close(); sky_img.close()
        if os.path.exists(temp_file): os.remove(temp_file)
        if os.path.exists(tmp_png): os.remove(tmp_png)
        gc.collect()
        
        return True, final_path, target_name_rus, ""

    except Exception as e:
        plt.close('all')
        if 'temp_file' in locals() and os.path.exists(temp_file): os.remove(temp_file)
        gc.collect()
        return False, str(e), "", ""
