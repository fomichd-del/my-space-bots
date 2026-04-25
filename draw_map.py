import ephem
import math
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

def generate_star_map(lat, lon, user_name="Исследователь"):
    # Настройки холста
    WIDTH, HEIGHT = 800, 800
    CENTER = (WIDTH // 2, HEIGHT // 2)
    RADIUS = 350
    
    # Цвета (в стиле твоего канала)
    BG_COLOR = (5, 10, 35)      # Глубокий космос
    HORIZON_COLOR = (40, 60, 120)
    STAR_COLOR = (255, 255, 255)
    TEXT_COLOR = (255, 215, 0)   # Золотистый

    # Создаем изображение
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Настройка наблюдателя
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.date = datetime.utcnow()
    obs.pressure = 0  # Игнорируем рефракцию для точности

    # Рисуем сетку горизонта
    draw.ellipse([CENTER[0]-RADIUS, CENTER[1]-RADIUS, CENTER[0]+RADIUS, CENTER[1]+RADIUS], 
                 outline=HORIZON_COLOR, width=2)

    # Список самых ярких звезд (можно дополнить из твоего stars_data.json)
    bright_stars = [
        "Sirius,f|S|A1,6:45:08.9,-16:42:58,1.46,2000",
        "Canopus,f|S|F0,6:23:57.1,-52:41:45,-0.72,2000",
        "Rigil Kentaurus,f|S|G2,14:39:35.9,-60:50:02,-0.01,2000",
        "Arcturus,f|S|K1,14:15:39.7,19:10:57,-0.04,2000",
        "Vega,f|S|A0,18:36:56.3,38:47:01,0.03,2000",
        "Capella,f|S|G5,5:16:41.4,45:59:53,0.08,2000",
        "Rigel,f|S|B8,5:14:32.3,-8:12:06,0.12,2000",
        "Procyon,f|S|F5,7:39:18.1,5:13:30,0.34,2000",
        "Betelgeuse,f|S|M1,5:55:10.3,7:24:25,0.45,2000",
        "Polaris,f|S|F7,2:31:48.7,89:15:51,1.97,2000"
    ]

    for star_data in bright_stars:
        star = ephem.readdb(star_data)
        star.compute(obs)

        # Рисуем только те, что выше горизонта (alt > 0)
        if star.alt > 0:
            # Математика полярной проекции
            # Высота (alt) определяет расстояние от центра (90 град - в центре)
            # Азимут (az) определяет угол
            r = RADIUS * (1 - (float(star.alt) / (math.pi / 2)))
            angle = float(star.az) - math.pi / 2
            
            x = CENTER[0] + r * math.cos(angle)
            y = CENTER[1] + r * math.sin(angle)

            # Размер звезды зависит от её яркости (magnitude)
            mag = float(star.mag)
            size = max(1, int(6 - mag)) 
            
            draw.ellipse([x-size, y-size, x+size, y+size], fill=STAR_COLOR)
            
            # Подписи для самых ярких
            if mag < 1.5:
                draw.text((x + 5, y + 5), star.name, fill=(150, 150, 150))

    # Добавляем Марти и информацию
    title_text = f"НЕБО НАД ТОБОЙ, {user_name.upper()}!"
    draw.text((30, 30), title_text, fill=TEXT_COLOR)
    draw.text((30, 60), f"Дата: {obs.date} UTC", fill=(100, 100, 100))
    draw.text((30, 740), "🐩 Марти: 'Смотри, сколько огней!'", fill=TEXT_COLOR)

    file_path = "user_sky_map.png"
    img.save(file_path)
    return file_path
