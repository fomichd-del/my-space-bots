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

# Глушим технические предупреждения
warnings.filterwarnings("ignore", category=FutureWarning)

TARGETS = {
    "ursa_major": [165, 56], "ursa_minor": [37, 89], "orion": [84, -5],
    "cassiopeia": [10, 59], "cygnus": [310, 45], "lyra": [279, 39],
    "aries": [31, 23], "taurus": [69, 16], "gemini": [114, 28],
    "cancer": [130, 20], "leo": [152, 12], "virgo": [201, -11]
}

def generate_star_map(lat, lon, user_name):
    gc.collect() 
    try:
        dt = datetime.now(timezone.utc)
        observer = Observer(dt=dt, lat=float(lat), lon=float(lon))
        
        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        target_key = random.choice(list(TARGETS.keys()))
        target_pos = TARGETS[target_key]
        # Берем русское название только для вывода в рамку "ЦЕЛЬ"
        target_name_rus = db.get(target_key, {}).get('name', target_key).split('(')[0].strip().upper()

        # Базовый стиль, который гарантированно работает
        style = PlotStyle().extend(extensions.BLUE_GOLD, extensions.GRADIENT_PRE_DAWN)

        # Рисуем саму карту в высоком качестве
        p = ZenithPlot(observer=observer, style=style, resolution=1400, autoscale=True)

        # Выводим все слои в оригинале
        p.horizon()
        p.milky_way()
        p.ecliptic()
        p.constellations() # Названия созвездий на английском
        p.stars(where=[_.magnitude < 5.3], where_labels=[_.magnitude < 2.3]) # Звезды на английском
        p.planets() # Планеты на английском

        # Целеуказатель
        p.marker(
            ra=target_pos[0], dec=target_pos[1],
            label="[ TARGET ]",
            style={
                "marker": {"size": 80, "symbol": "circle", "fill": "none", "edge_color": "#FF00FF", "edge_width": 3, "line_style": [1, [5, 5]]},
                "label": {"font_size": 24, "font_weight": 800, "font_color": "#FF00FF", "offset_y": 50}
            }
        )

        temp_file = "v30_tmp.png"
        p.export(temp_file, transparent=True, padding=0.01)
        plt.close('all')

        # --- РАСЧЕТ ЭФЕМЕРИД ДЛЯ НИЖНЕЙ ПАНЕЛИ ---
        e_obs = ephem.Observer()
        e_obs.lat, e_obs.lon, e_obs.date = str(lat), str(lon), datetime.now()
        
        moon = ephem.Moon()
        moon.compute(e_obs)
        moon_phase = int(moon.phase)
        
        sun = ephem.Sun()
        sun.compute(e_obs)
        try:
            rise_time = ephem.localtime(e_obs.next_rising(sun)).strftime('%H:%M')
            set_time = ephem.localtime(e_obs.next_setting(sun)).strftime('%H:%M')
        except:
            rise_time, set_time = "--:--", "--:--"

        # === ФИНАЛЬНАЯ СБОРКА И ИДЕАЛЬНАЯ ЦЕНТРОВКА ===
        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_file).convert("RGBA")
        
        # Оставляем идеальный размер из v29 (880px)
        sky_size = 880
        sky_img = sky_img.resize((sky_size, sky_size), Image.Resampling.LANCZOS)
        
        # Оставляем идеальную центровку из v29
        x_offset = (bg_img.width - sky_size) // 2
        y_offset = 360
        bg_img.paste(sky_img, (x_offset, y_offset), sky_img)
        
        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.imshow(bg_img); ax_bg.axis('off')

        t_col = '#D4E6FF'
        
        # Данные в нижние рамки
        fig.text(0.38, 0.170, user_name.upper(), color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.106, f"{moon_phase}%", color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.40, 0.067, rise_time, color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.74, 0.067, set_time, color=t_col, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=22, fontweight='bold')

        path = f"sky_final_v30.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0, dpi=dpi)
        
        plt.close('all')
        bg_img.close(); sky_img.close()
        if os.path.exists(temp_file): os.remove(temp_file)
        gc.collect()
        
        return True, path, target_name_rus, ""

    except Exception as e:
        plt.close('all')
        gc.collect()
        return False, str(e), "", ""
