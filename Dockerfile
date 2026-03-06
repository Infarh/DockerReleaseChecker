# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем конфигурацию и исходный код
COPY config.json .
COPY src/ ./src/

# Создаем директорию для скачанных файлов
RUN mkdir -p /downloads

# Объявляем volume для скачанных файлов
VOLUME ["/downloads"]

# Запускаем приложение с unbuffered выводом для логов
CMD ["python", "-u", "-m", "src.main"]
