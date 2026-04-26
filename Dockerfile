# Используем стабильный образ Python
FROM python:3.9-slim

# Устанавливаем системные библиотеки (ОБНОВЛЕНО: libtiff6 вместо libtiff5)
RUN apt-get update && apt-get install -y \
    libopenjp2-7 \
    libtiff6 \
    && rm -rf /var/lib/apt/lists/*

# Указываем рабочую папку
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт 7860 для Hugging Face
EXPOSE 7860

# Запускаем Мартина
CMD ["python", "main.py"]
