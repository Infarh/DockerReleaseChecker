# Health Check для Docker Release Checker

## Описание

Контейнер Docker Release Checker оснащён встроенной системой мониторинга работоспособности (health check), которая позволяет Docker автоматически отслеживать состояние приложения.

## Как это работает

Health check выполняет следующие проверки:

1. **Первый запуск**: Если timestamp файл ещё не существует, health check возвращает `OK` (приложение запущено, ожидается первая проверка)

2. **Регулярная работа**: Проверяет, что последняя проверка релизов была выполнена не слишком давно:
   - Читает timestamp последней проверки из файла `/downloads/.last_check_timestamp.json`
   - Вычисляет время, прошедшее с последней проверки
   - Сравнивает с допустимым порогом (3× интервал проверки из конфигурации)

3. **Определение статуса**:
   - ✅ **healthy**: Последняя проверка выполнялась в пределах допустимого времени
   - ❌ **unhealthy**: Прошло слишком много времени с последней проверки (возможно, приложение зависло)

## Параметры Health Check

### В Dockerfile:
```dockerfile
HEALTHCHECK --interval=2m --timeout=10s --start-period=30s --retries=3 \
    CMD python -m src.healthcheck || exit 1
```

### В docker-compose.yml:
```yaml
healthcheck:
  test: ["CMD", "python", "-m", "src.healthcheck"]
  interval: 2m       # Проверка каждые 2 минуты
  timeout: 10s       # Таймаут команды проверки
  start_period: 30s  # Период инициализации (не считается как failure)
  retries: 3         # Количество неудач для статуса unhealthy
```

## Использование

### Проверка статуса контейнера

```bash
# Просмотр статуса всех контейнеров
docker ps

# Подробная информация о health check
docker inspect docker-release-checker --format='{{json .State.Health}}'

# Просмотр логов health check
docker inspect docker-release-checker | jq '.[0].State.Health.Log'
```

### Статусы контейнера

- **starting**: Контейнер запущен, идёт период инициализации (start-period)
- **healthy**: Все проверки проходят успешно
- **unhealthy**: 3 проверки подряд провалились

### Интеграция с системами мониторинга

Docker может автоматически перезапускать unhealthy контейнеры при использовании orchestration систем:

**Docker Swarm:**
```yaml
deploy:
  restart_policy:
    condition: on-failure
    max_attempts: 3
```

**Kubernetes:**
```yaml
livenessProbe:
  exec:
    command:
    - python
    - -m
    - src.healthcheck
  initialDelaySeconds: 30
  periodSeconds: 120
  timeoutSeconds: 10
  failureThreshold: 3
```

### Мониторинг через alerting системы

Health check можно интегрировать с системами мониторинга:

**Prometheus + cAdvisor:**
```promql
# Alert при unhealthy контейнере
container_health_status{name="docker-release-checker"} != 1
```

**Zabbix:**
```bash
# Item для мониторинга
docker inspect docker-release-checker --format='{{.State.Health.Status}}'
```

## Логирование

Health check выводит подробную информацию при каждой проверке:

```
OK: Последняя проверка была 45.2 минут назад
```

или

```
FAIL: Последняя проверка была 185.7 минут назад (допустимо до 180.0 минут)
```

## Пороги определения unhealthy

По умолчанию используется коэффициент **3× интервал проверки**:

- Интервал проверки: 1 час (3600 сек)
- Максимально допустимая задержка: 3 часа (10800 сек)

Это позволяет контейнеру пережить:
- Кратковременные проблемы с сетью
- Гибернацию хоста до 3 часов
- Задержки при скачивании больших файлов

## Ручная проверка

Выполнить health check вручную внутри контейнера:

```bash
docker exec docker-release-checker python -m src.healthcheck
echo $?  # 0 = healthy, 1 = unhealthy
```

## Отладка

Если health check показывает unhealthy:

1. **Проверьте логи приложения:**
   ```bash
   docker logs docker-release-checker --tail 100
   ```

2. **Проверьте timestamp файл:**
   ```bash
   docker exec docker-release-checker cat /downloads/.last_check_timestamp.json
   ```

3. **Проверьте процесс Python:**
   ```bash
   docker exec docker-release-checker ps aux
   ```

4. **Проверьте сетевое подключение:**
   ```bash
   docker exec docker-release-checker ping -c 3 docs.docker.com
   ```

## Отключение Health Check

Если необходимо отключить health check:

**В docker-compose.yml:**
```yaml
healthcheck:
  disable: true
```

**При запуске контейнера:**
```bash
docker run --no-healthcheck ...
```

## Тестирование

Запуск тестов health check:

```bash
pytest tests/test_healthcheck.py -v
```

Все тесты включают проверку различных сценариев:
- Первый запуск без timestamp
- Недавняя успешная проверка
- Задержка в пределах нормы
- Критическая задержка
- Невалидные данные
- Отсутствие конфигурации
