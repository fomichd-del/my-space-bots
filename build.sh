#!/usr/bin/env bash
# Останавливаем сборку при любой ошибке
set -o errexit

# 1. Устанавливаем библиотеки
pip install -r requirements.txt

# 2. Проверяем наличие папки data
mkdir -p data

# 3. Скачиваем большой файл звезд прямо на диск сервера
# Флаг -nc (no-clobber) не даст скачивать файл заново, если он уже есть
wget -nc -O data/stars.bigksy.0.1.3.mag11.parquet https://github.com/steveberardi/starplot-bigsky/releases/download/v0.1.3/stars.bigksy.0.1.3.mag11.parquet
