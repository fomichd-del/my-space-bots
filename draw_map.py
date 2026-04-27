import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import ZenithPlot, Observer, _
from starplot.styles import PlotStyle, extensions
from datetime import datetime
import os, json, random
from PIL import Image
import ephem

# База координат целей (RA, DEC)
TARGETS = {
    "ursa_major": [165.0, 56.0], "ursa_minor": [37.0, 89.0], "orion": [84.0, -5.0],
    "cassiopeia": [10.0, 59.0], "leo": [152.0, 12.0], "cygnus": [310.0, 45.0],
    "gemini": [114.0, 28.0], "taurus": [69.0, 16.0], "lyra": [279.0, 39.0],
    "andromeda": [10.0, 41.0], "pegasus": [345.0, 15.0], "bootes": [214.0, 19.0]
}

def generate_star_map(lat, lon, user_name):
    try:
        dt = datetime.utcnow()
        observer = Observer(dt=dt, lat=float(lat), lon=float(lon))

        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        target_key = random.choice(list(TARGETS.keys()))
        target_pos = TARGETS[target_key]
        target_name_rus = db[target_key]['name'].split('(')[0].strip().upper()

        # --- СТИЛЬ BLUE_GOLD С КРУПНЫМИ ШРИФТАМИ ---
        custom_style = PlotStyle().extend(
            extensions.BLUE_GOLD,
            extensions.GRADIENT_PRE_DAWN,
            {
                "star": {
                    "label": {"font_size": 12, "font_weight": 500} # Крупные имена звезд
                },
                "constellation": {
                    "label": {"font_size": 18, "font_weight": 700}, # Крупные созвездия
                    "line": {"stroke_width": 3.0} # Жирные линии
                },
                "planet": {
                    "label": {"font_size": 16, "font_weight": 700} # Крупные планеты
                }
            }
        )

        p = ZenithPlot(
            observer=observer,
            style=custom_style,
            resolution=2800, # Ультра-качество
            autoscale=True,
        )

        # РИСУЕМ СЛОИ
        p.horizon()
        p.constellations()
        p.constellation_labels()
        p.milky_way()      # Космическая пыль
        p.ecliptic()       # Линия эклиптики
        
        # Звезды (видимость до 5.5 звездной величины)
        p.stars(where=[_.magnitude < 5.5], where_labels=[_.magnitude < 3.0])
        
        # DSO (Галактики и скопления)
        p.galaxies(where=[_.magnitude < 9], where_labels=[False])
        p.open_clusters(where=[_.magnitude < 9], where_labels=[False])

        p.sun(label="СОЛНЦЕ")
        p.moon(label="ЛУНА")
        p.planets()

        # ЦЕЛЬ (Маркер-прицел)
        p.marker(
            ra=target_pos[0],
            dec=target_pos[1],
            style={
                "marker": {
                    "size": 90,
                    "symbol": "circle",
                    "fill": "none",
                    "edge_color": "#FF00FF",
                    "edge_width": 4,
                    "line_style": [1, [6, 6]],
                    "zorder": 500,
                },
                "label": {
                    "font_size": 28,
                    "font_weight": 800,
                    "font_color": "#FF00FF",
                    "offset_y": 60,
                },
            },
            label="[ ЦЕЛЬ ]",
        )

        # ЭКСПОРТ И СБОРКА
        temp_sky = "zenith_sky.png"
        p.export(temp_sky, transparent=True, padding=0.1)

        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_sky).convert("RGBA")
        sky_img = sky_img.resize((1060, 1060))
        bg_img.paste(sky_img, (200, 360), sky_img) # Точная центровка

        # Финальный текст (Твоя калибровка 22px)
        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.imshow(bg_img)
        ax_bg.axis('off')

        # Данные для рамок
        e_obs = ephem.Observer(); e_obs.lat, e_obs.lon, e_obs.date = str(lat), str(lon), dt
        moon, sun = ephem.Moon(), ephem.Sun()
        moon.compute(e_obs); sun.compute(e_obs)
        rise = ephem.localtime(e_obs.next_rising(sun)).strftime('%H:%M')
        sset = ephem.localtime(e_obs.next_setting(sun)).strftime('%H:%M')

        fig.text(0.38, 0.170, user_name.upper(), color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.38, 0.106, f"Фаза: {int(moon.phase)}%", color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.40, 0.067, rise, color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.74, 0.067, sset, color='#D4E6FF', fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=22, fontweight='bold')

        path = f"sky_{dt.strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0)
        plt.close()
        
        if os.path.exists(temp_sky): os.remove(temp_sky)
        return True, path, target_name_rus, ""

    except Exception as e:
        return False, str(e), "", ""
