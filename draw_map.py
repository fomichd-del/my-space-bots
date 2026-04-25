import ephem
import math
from PIL import Image, ImageDraw
from datetime import datetime

def generate_star_map(lat, lon, user_name="Исследователь"):
    # Настройки холста
    WIDTH, HEIGHT = 800, 800
    CENTER = (400, 400)
    RADIUS = 350
    
    # Цвета
    BG_COLOR = (5, 10, 35)      # Глубокий космос
    HORIZON_COLOR = (40, 60, 120)
    STAR_COLOR = (255, 255, 255)

    # Создаем изображение
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Настройка наблюдателя
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.date = datetime.utcnow()
    obs.pressure = 0 

    # Рисуем круг горизонта
    draw.ellipse([CENTER[0]-RADIUS, CENTER[1]-RADIUS, CENTER[0]+RADIUS, CENTER[1]+RADIUS], 
                 outline=HORIZON_COLOR, width=3)

    # Список ключевых звезд
    bright_stars = [
        "Sirius,f|S|A1,6:45:08.9,-16:42:58,1.46,2000",
        "Vega,f|S|A0,18:36:56.3,38:47:01,0.03,2000",
        "Polaris,f|S|F7,2:31:48.7,89:15:51,1.97,2000",
        "Betelgeuse,f|S|M1,5:55:10.3,7:24:25,0.45,2000",
        "Rigel,f|S|B8,5:14:32.3,-8:12:06,0.12,2000",
        "Arcturus,f|S|K1,14:15:39.7,19:10:57,-0.04,2000",
        "Capella,f|S|G5,5:16:41.4,45:59:53,0.08,2000"
    ]

    for star_data in bright_stars:
        star = ephem.readdb(star_data)
        star.compute(obs)

        if star.alt > 0:
            # Проекция на плоскость
            r = RADIUS * (1 - (float(star.alt) / (math.pi / 2)))
            angle = float(star.az) - math.pi / 2
            
            x = CENTER[0] + r * math.cos(angle)
            y = CENTER[1] + r * math.sin(angle)

            # Рисуем звезду
            size = max(1, int(6 - float(star.mag)))
            draw.ellipse([x-size, y-size, x+size, y+size], fill=STAR_COLOR)
            
            # Подпись звезды
            if float(star.mag) < 1.0:
                draw.text((x + 7, y), star.name, fill=(180, 180, 180))

    # Текстовые метки
    draw.text((30, 30), f"НЕБО НАД ТОБОЙ: {user_name.upper()}", fill=(255, 215, 0))
    draw.text((30, 750), "🐩 Марти: 'Смотри, это звезды прямо над нами!'", fill=(255, 215, 0))

    file_path = "user_sky.png"
    img.save(file_path)
    return file_path
