import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from starplot import MapProjection, ZenithMap
from starplot.styles import PlotStyle, l_blue, set_style
from datetime import datetime
import os, json, random
from PIL import Image
import ephem

# Список созвездий для выбора цели (названия по стандарту IAU)
IAU_CONSTELLATIONS = [
    "Ursa Major", "Ursa Minor", "Orion", "Cassiopeia", "Leo", "Cygnus", 
    "Gemini", "Taurus", "Lyra", "Aquila", "Andromeda", "Pegasus", 
    "Perseus", "Auriga", "Bootes", "Virgo", "Aries", "Scorpius"
]

def get_moon_phase(obs):
    m = ephem.Moon(obs)
    return int(m.phase)

def generate_star_map(lat, lon, user_name):
    try:
        now = datetime.utcnow()
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = now

        # Загружаем твои описания
        with open('constellations.json', 'r', encoding='utf-8') as f:
            db = json.load(f)

        # Выбираем случайную цель из тех, что мы знаем в JSON
        target_key = random.choice(list(db.keys()))
        target_name_rus = db[target_key]['name'].split('(')[0].strip().upper()

        # Настройка стилей Starplot (Неоновый стиль)
        style = PlotStyle().extend(
            set_style.BIG_CITY, # Базовый стиль для яркости
            {
                "star": {
                    "label": {"font_size": 10, "font_color": "#ffffff", "font_alpha": 0.7},
                    "marker": {"fill_color": "#ffffff", "alpha": 0.9}
                },
                "constellation": {
                    "line": {"stroke_color": "#FFD700", "stroke_width": 2.5, "extra_glow": True},
                    "label": {"font_size": 16, "font_color": "#FFD700", "font_weight": "bold"}
                },
                "background_color": "#0B0D14"
            }
        )

        # Создаем карту Зенита (то, что прямо над головой)
        p = ZenithMap(
            lat=float(lat),
            lon=float(lon),
            dt=now,
            style=style,
            resolution=2000,
            hide_colliding_labels=True
        )

        # Рисуем всё сразу: звезды, созвездия, границы
        p.draw_stars(mag_limit=5.5) # Видим даже не очень яркие звезды
        p.draw_constellations()
        p.draw_constellation_borders(stroke_color="#4A90E2", alpha=0.2)
        
        # Подсвечиваем планеты
        p.draw_planets(label_font_size=14, marker_size=100)

        # Сохраняем временный файл
        temp_sky = "temp_sky.png"
        p.export(temp_sky)

        # Накладываем на твой фон background1.png
        bg_img = Image.open('background1.png')
        sky_img = Image.open(temp_sky).convert("RGBA")
        
        # Изменяем размер неба под твой круг
        sky_img = sky_img.resize((1200, 1200)) # Примерный размер круга
        bg_img.paste(sky_img, (150, 320), sky_img) # Позиция круга на фоне

        # Добавляем твой текст (Калибровка 22px)
        # Для простоты используем matplotlib поверх финальной картинки
        dpi = 100
        fig = plt.figure(figsize=(bg_img.width/dpi, bg_img.height/dpi), dpi=dpi)
        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.imshow(bg_img)
        ax_bg.axis('off')

        moon = ephem.Moon(); moon.compute(obs)
        sun = ephem.Sun(); sun.compute(obs)
        rise = ephem.localtime(obs.next_rising(sun)).strftime('%H:%M')
        sset = ephem.localtime(obs.next_setting(sun)).strftime('%H:%M')

        # Твои рамки текста
        t_color = '#D4E6FF'
        fig.text(0.38, 0.170, user_name.upper(), color=t_color, fontsize=22, fontweight='bold')
        fig.text(0.49, 0.135, f"{float(lat):.2f}N, {float(lon):.2f}E", color=t_color, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.106, f"Фаза: {int(moon.phase)}%", color=t_color, fontsize=22, fontweight='bold')
        fig.text(0.40, 0.067, rise, color=t_color, fontsize=22, fontweight='bold')
        fig.text(0.74, 0.067, sset, color=t_color, fontsize=22, fontweight='bold')
        fig.text(0.38, 0.028, target_name_rus, color='#FF00FF', fontsize=22, fontweight='bold')

        path = f"sky_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(path, bbox_inches='tight', pad_inches=0)
        plt.close()
        
        os.remove(temp_sky)
        return True, path, target_name_rus, ""

    except Exception as e:
        return False, str(e), "", ""
