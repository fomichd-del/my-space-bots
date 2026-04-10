name: earth_bot.py

on:
  schedule:
    # Запуск в 10:30 UTC (13:30 по МСК)
    - cron: '30 10 * * *'
  workflow_dispatch:      # Кнопка для ручного запуска

jobs:
  build:
    runs-on: ubuntu-latest
    
    permissions:
      contents: write # Разрешение на сохранение файла памяти

    steps:
      - name: Checkout code
        uses: actions/checkout@v3
    
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
    
      - name: Install dependencies
        run: |
          pip install requests deep_translator
        
      - name: Run earth_bot.py
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          NASA_API_KEY: ${{ secrets.NASA_API_KEY }}
        run: python earth_bot.py

      - name: Save memory
        run: |
          git config --global user.name "GitHub Action Bot"
          git config --global user.email "actions@github.com"
          # Добавляем файл истории в индекс
          git add last_earth_id.txt
          # Фиксируем изменения
          git commit -m "Update Earth memory: $(date)" || echo "No changes to commit"
          # Синхронизация и пуш
          git pull --rebase origin main
          git push origin main
