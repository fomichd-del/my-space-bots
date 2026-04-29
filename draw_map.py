import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime, timezone
import os, json, random, gc
from PIL import Image
import ephem
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

TARGETS = {
    "ursa_major": [165, 56], "ursa_minor": [37, 89], "orion": [84, -5],
    "cassiopeia": [10, 59], "cygnus": [310, 45], "lyra": [279, 39],
    "aries": [31, 23], "taurus": [69, 16], "gemini": [114, 28],
    "cancer": [130, 20], "leo": [152, 12], "virgo": [201, -11]
}

# Добавлен параметр user_id
def generate_star_map(lat, lon, user_name, user_id):
    gc.collect() 
    # Уникальные имена файлов для каждого штурмана
    temp_file = f"tmp_{user_id}.png"
    final_path = f"sky_{user_id}.jpg" # Перешли на JPG для легкости
    
    try:
        dt = datetime.now(timezone.utc)
        observer = Observer(dt=dt, lat=float(lat), lon=float(lon))
        
        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        target_key = random.choice(list(TARGETS.keys()))
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

        e_obs = ephem.Observer()
        e_obs.lat, e_obs.lon, e_obs.date = str(lat), str(lon), datetime.now()
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

        # Сохраняем как JPG (уменьшаем вес в 5-7 раз)
        # Сначала конвертируем всё в RGB, так как JPG не поддерживает прозрачность
        plt.savefig(final_path.replace(".jpg", ".png"), bbox_inches='tight', pad_inches=0, dpi=dpi)
        plt.close('all')
        
        final_img = Image.open(final_path.replace(".jpg", ".png")).convert("RGB")
        final_img.save(final_path, "JPEG", quality=85, optimize=True)
        
        # Удаляем лишние хвосты
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
