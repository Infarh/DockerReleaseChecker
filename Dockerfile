# Этап 1: выполнение тестов; при падении тестов сборка прерывается
FROM python:3.11-slim AS test

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt requirements-dev.txt .

# Устанавливаем runtime и test зависимости
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Копируем исходный код и тесты
COPY src/ ./src/
COPY tests/ ./tests/
COPY pytest.ini ./

# Если тесты не прошли, docker build завершится ошибкой
RUN pytest -q && touch /tmp/.tests-passed

# Этап 2: финальный runtime-образ
FROM python:3.11-slim AS runtime

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем только runtime зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Привязываем runtime к test-stage, чтобы этап тестов не пропускался
COPY --from=test /tmp/.tests-passed /tmp/.tests-passed

# Копируем конфигурацию и исходный код
COPY config.json .
COPY src/ ./src/

# Создаем директорию для скачанных файлов
RUN mkdir -p /downloads

# Объявляем volume для скачанных файлов
VOLUME ["/downloads"]

# Запускаем приложение с unbuffered выводом для логов
CMD ["python", "-u", "-m", "src.main"]
