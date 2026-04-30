#!/usr/bin/env bash
set -o errexit

# 1. Устанавливаем библиотеки из твоего специального файла
# Мы просто перенесли эту команду сюда
pip install -r render_reqs.txt

# 2. Создаем папку для данных
mkdir -p data

# 3. Скачиваем большой файл звезд прямо на диск
wget -nc -O data/stars.bigksy.0.1.3.mag11.parquet https://github.com/steveberardi/starplot-bigsky/releases/download/v0.1.3/stars.bigksy.0.1.3.mag11.parquet
