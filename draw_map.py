import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime, timezone
import os, json, random, gc, math
from PIL import Image, ImageEnhance, ImageDraw, ImageChops
import ephem
import warnings
from timezonefinder import TimezoneFinder
import pytz
import requests
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

# --- [ КОНФИГУРАЦИЯ ПУТЕЙ ] ---
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# База координат целей
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

def get_cloud_cover(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=cloud_cover"
        response = requests.get(url, timeout=5)
        return int(response.json()['current']['cloud_cover'])
    except: return 0

def generate_star_map(lat, lon, user_name, user_id):
    gc.collect() 
    temp_raw_star = OUTPUT_DIR / f"raw_{user_id}.png"
    final_png = OUTPUT_DIR / f"fin_{user_id}.png"
    final_jpg = OUTPUT_DIR / f"sky_{user_id}.jpg"
    
    try:
        dt_now = datetime.now(timezone.utc)
        observer = Observer(dt=dt_now, lat=float(lat), lon=float(lon))
        cloud_cover = get_cloud_cover(lat, lon)
        
        # Загрузка базы имен созвездий
        const_json_path = BASE_DIR / 'constellations.json'
        with open(const_json_path, 'r', encoding='utf-8') as f:
            db = json.load(f)

        e_obs = ephem.Observer()
        e_obs.lat, e_obs.lon = str(lat), str(lon)
        e_obs.date = dt_now
        
        visible_targets = []
        for key, pos in TARGETS.items():
            body = ephem.FixedBody()
            body._ra = math.radians(pos[0]); body._dec = math.radians(pos[1])
            body.compute(e_obs)
            if math.degrees(body.alt) > 10: visible_targets.append(key)

        target_key = random.choice(visible_targets) if visible_targets else "ursa_major"
        target_pos = TARGETS[target_key]
        target_name_rus = db.get(target_key, {}).get('name', target_key).split('(')[0].strip().upper()

        # --- [ ИСПРАВЛЕННЫЙ СТИЛЬ ] ---
        style = PlotStyle().extend(extensions.BLUE_GOLD, extensions.GRADIENT_PRE_DAWN)
        
        # В Starplot v0.10+ используются единственные числа: star и constellation
        style.star.label.font_size = 11
        style.constellation.label.font_size = 16
        style.constellation.line.width = 2.5
        style.constellation.line.color = "#5c9dff"

        p = ZenithPlot(observer=observer, style=style, resolution=2000, autoscale=True)
        p.horizon()
        p.milky_way() 
        p.constellations()
        p.ecliptic(style={"line": {"color": "#FF4444", "width": 2.0, "alpha": 0.85}})
        p.celestial_equator(style={"line": {"color": "#4477FF", "width": 2.0, "alpha": 0.85}})
        p.constellation_labels() 
        p.stars(where=[_.magnitude < 6.2], where_labels=[_.magnitude < 3.5]) 
        p.planets() 

        # Светила
        sun_e = ephem.Sun(); sun_e.compute(e_obs)
        moon_e = ephem.Moon(); moon_e.compute(e_obs)
        sun_j = ephem.Equatorial(sun_e, epoch='2000')
        moon_j = ephem.Equatorial(moon_e, epoch='2000')
        
        p.marker(ra=math.degrees(sun_j.ra), dec=math.degrees(sun_j.dec), label="СОЛНЦЕ",
                 style={"marker": {"size": 46, "symbol": "circle", "color": "#FFCC00"}, "label": {"font_size": 18, "font_color": "#FFCC00"}})
        
        p.marker(ra=math.degrees(moon_j.ra), dec=math.degrees(moon_j.dec), label="ЛУНА",
                 style={"marker": {"size": 52, "symbol": "circle", "color": "#FFFEE0"}, "label": {"font_size": 20, "font_color": "#FFFEE0"}})

        p.marker(ra=target_pos[0], dec=target_pos[1], label="ЦЕЛЬ!",
                 style={"marker": {"size": 110, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 4},
                        "label": {"font_size": 26, "font_weight": 700, "font_color": "#FF00FF", "offset_y": 65}})

        p.export(str(temp_raw_star), transparent=True, padding=0.01)
        plt.clf(); plt.close('all')

        # --- [ ОБРАБОТКА PIL ] ---
        bg_img = Image.open(BASE_DIR / 'background1.png')
        sky_img = Image.open(temp_raw_star).convert("RGBA")
        sky_size = 940 
        sky_img = sky_img.resize((sky_size, sky_size), Image.Resampling.LANCZOS)
        
        cloud_path = BASE_DIR / 'clouds.png'
        if cloud_cover > 5 and cloud_path.exists():
            try:
                clouds_tex = Image.open(cloud_path).convert('RGBA').resize((sky_size, sky_size))
                cloud_mask = ImageEnhance.Contrast(clouds_tex.convert('L')).enhance(1.8)
                cloud_mask = cloud_mask.point(lambda x: int(x * (cloud_cover / 100.0)))
                circle_mask = Image.new("L", (sky_size, sky_size), 0)
                ImageDraw.Draw(circle_mask).ellipse((65, 65, sky_size-65, sky_size-65), fill=255)
                final_cloud_mask = ImageChops.multiply(cloud_mask, circle_mask)
                cloud_overlay = Image.new('RGBA', (sky_size, sky_size), (240, 240, 245))
                cloud_overlay.putalpha(final_cloud_mask)
                sky_img = Image.alpha_composite(sky_img, cloud_overlay)
            except: pass

        bg_img.paste(sky_img, ((bg_img.width - sky_size)//2, 360 - ((sky_size - 880)//2)), sky_img)
        
        dpi = 300 
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(bg_img); ax.axis('off')

        try:
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lng=float(lon), lat=float(lat))
            user_tz = pytz.timezone(tz_name) if tz_name else pytz.utc
            rise_t = ephem.localtime(e_obs.next_rising(sun_e)).strftime('%H:%M')
            set_t = ephem.localtime(e_obs.next_setting(sun_e)).strftime('%H:%M')
        except: rise_t, set_t = "--:--", "--:--"

        t_col = '#D4E6FF'
        fig.text(0.38, 0.175, user_name.upper(), color=t_col, fontsize=8)
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_col, fontsize=8)
        fig.text(0.32, 0.106, f"Фаза: {int(moon_e.phase)}% | Облачность: {cloud_cover}%", color=t_col, fontsize=8)
        fig.text(0.385, 0.072, rise_t, color=t_col, fontsize=8)
        fig.text(0.705, 0.072, set_t, color=t_col, fontsize=8)
        fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=8, fontweight='bold')

        plt.savefig(str(final_png), bbox_inches='tight', pad_inches=0, dpi=dpi)
        plt.close(fig)
        
        with Image.open(final_png) as img:
            img.convert("RGB").save(str(final_jpg), "JPEG", quality=90, optimize=True)
        
        if temp_raw_star.exists(): os.remove(temp_raw_star)
        bg_img.close(); sky_img.close()
        gc.collect()
        
        return True, str(final_jpg), str(final_png), target_name_rus, ""

    except Exception as e:
        plt.close('all')
        return False, "", "", "", str(e)
