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
from timezonefinder import TimezoneFinder
import pytz

warnings.filterwarnings("ignore", category=FutureWarning)

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
        dt_now = datetime.now(timezone.utc)
        observer = Observer(dt=dt_now, lat=float(lat), lon=float(lon))
        
        with open('constellations.json', 'r', encoding='utf-8') as f:
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

        style = PlotStyle().extend(extensions.BLUE_GOLD, extensions.GRADIENT_PRE_DAWN)
        try:
            style.stars.label.font_size = 11
            style.constellations.label.font_size = 16
            style.constellations.line.width = 2.5
            style.constellations.line.color = "#5c9dff"
        except: pass

        p = ZenithPlot(observer=observer, style=style, resolution=2000, autoscale=True)

        p.horizon()
        p.milky_way() 
        p.constellations()
        
        p.ecliptic(style={"line": {"color": "#FF4444", "width": 2.0, "alpha": 0.85}})
        p.celestial_equator(style={"line": {"color": "#4477FF", "width": 2.0, "alpha": 0.85}})
        
        p.constellation_labels() 
        p.stars(where=[_.magnitude < 6.2], where_labels=[_.magnitude < 3.5]) 
        
        p.planets() 

        # --- [ СВЕТИЛА: ПРАВИЛЬНЫЕ ГРАДУСЫ (БЕЗ ДЕЛЕНИЯ НА 15!) ] ---
        sun_e = ephem.Sun(); sun_e.compute(e_obs)
        moon_e = ephem.Moon(); moon_e.compute(e_obs)
        
        sun_j2000 = ephem.Equatorial(sun_e, epoch='2000')
        moon_j2000 = ephem.Equatorial(moon_e, epoch='2000')
        
        # СОЛНЦЕ (Полностью твой рабочий код координат)
        p.marker(
            ra=math.degrees(sun_j2000.ra), 
            dec=math.degrees(sun_j2000.dec), 
            label="СОЛНЦЕ",
            style={
                "marker": {"size": 46, "symbol": "circle", "color": "#FFCC00", "edge_color": "#FF8800", "edge_width": 2},
                "label": {"font_size": 18, "font_weight": 700, "font_color": "#FFCC00", "offset_y": 30}
            }
        )
        
        # ЛУНА (Без деления на 15, но с крупным размером и подписью)
        p.marker(
            ra=math.degrees(moon_j2000.ra), 
            dec=math.degrees(moon_j2000.dec), 
            label="ЛУНА",
            style={
                "marker": {"size": 52, "symbol": "circle", "color": "#FFFEE0", "edge_color": "#BBBBBB", "edge_width": 2},
                "label": {"font_size": 20, "font_weight": 900, "font_color": "#FFFEE0", "offset_y": 30}
            }
        )

        # ЦЕЛЬ (Без деления на 15)
        p.marker(
            ra=target_pos[0], 
            dec=target_pos[1], 
            label="ЦЕЛЬ!",
            style={
                "marker": {"size": 110, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 4},
                "label": {"font_size": 26, "font_weight": 700, "font_color": "#FF00FF", "offset_y": 65}
            }
        )

        p.export(temp_file, transparent=True, padding=0.01)
        plt.close('all')

        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_file).convert("RGBA")
        sky_size = 940 
        sky_img = sky_img.resize((sky_size, sky_size), Image.Resampling.LANCZOS)
        bg_img.paste(sky_img, ((bg_img.width - sky_size)//2, 360 - ((sky_size - 880)//2)), sky_img)
        
        dpi = 300 
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(bg_img); ax.axis('off')

        try:
            rise_utc = e_obs.next_rising(sun_e).datetime()
            set_utc = e_obs.next_setting(sun_e).datetime()
            tf = TimezoneFinder(in_memory=False)
            timezone_str = tf.timezone_at(lng=float(lon), lat=float(lat))
            if timezone_str:
                user_tz = pytz.timezone(timezone_str)
                rise_time = pytz.utc.localize(rise_utc).astimezone(user_tz).strftime('%H:%M')
                set_time = pytz.utc.localize(set_utc).astimezone(user_tz).strftime('%H:%M')
            else:
                rise_time, set_time = rise_utc.strftime('%H:%M'), set_utc.strftime('%H:%M')
        except: rise_time, set_time = "--:--", "--:--"

        t_col = '#D4E6FF'
        fig.text(0.38, 0.175, user_name.upper(), color=t_col, fontsize=8, fontweight='normal')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_col, fontsize=8, fontweight='normal')
        fig.text(0.35, 0.106, f"Фаза: {int(moon_e.phase)}%", color=t_col, fontsize=8, fontweight='normal')
        fig.text(0.385, 0.072, rise_time, color=t_col, fontsize=8, fontweight='normal')
        fig.text(0.705, 0.072, set_time, color=t_col, fontsize=8, fontweight='normal')
        fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=8, fontweight='normal')

        tmp_png = f"fin_{user_id}.png"
        plt.savefig(tmp_png, bbox_inches='tight', pad_inches=0, dpi=dpi)
        plt.close(fig)
        
        with Image.open(tmp_png) as img:
            img.convert("RGB").save(final_path, "JPEG", quality=98, optimize=True)
        
        bg_img.close(); sky_img.close()
        for f in [temp_file, tmp_png]:
            if os.path.exists(f): os.remove(f)
        gc.collect()
        
        return True, final_path, target_name_rus, ""

    except Exception as e:
        plt.close('all')
        return False, str(e), "", ""
