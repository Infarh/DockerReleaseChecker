# Этап 1: выполнение тестов; при падении тестов сборка прерывается
FROM python:3.14.3-slim AS test

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
FROM python:3.14.3-slim AS runtime

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

# Настраиваем health check для мониторинга работоспособности контейнера
# - интервал: проверка каждые 2 минуты
# - timeout: таймаут команды проверки 10 секунд
# - start-period: 30 секунд на инициализацию приложения
# - retries: 3 неудачные попытки подряд для статуса unhealthy
HEALTHCHECK --interval=2m --timeout=10s --start-period=30s --retries=3 \
    CMD python -m src.healthcheck || exit 1

# Запускаем приложение с unbuffered выводом для логов
CMD ["python", "-u", "-m", "src.main"]
