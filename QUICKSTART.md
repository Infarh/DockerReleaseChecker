# Быстрый старт Docker Release Checker

## Запуск за 3 шага

### 1. Настройте конфигурацию

Отредактируйте `config.json` согласно примерам в [CONFIG_EXAMPLES.md](CONFIG_EXAMPLES.md)

### 2. Запустите в Docker

```bash
docker-compose up -d
```

### 3. Проверьте логи

```bash
docker-compose logs -f
```

## Управление

**Остановка:**
```bash
docker-compose down
```

**Перезапуск:**
```bash
docker-compose restart
```

**Просмотр скачанных файлов:**
```bash
ls -la ./downloads/
```

## Изменение конфигурации

Конфигурация перечитывается автоматически при каждой проверке - просто отредактируйте `config.json` и дождитесь следующего цикла проверки (или перезапустите контейнер).

## Локальная разработка

```bash
# Создание и активация venv
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac

# Установка зависимостей
pip install -r requirements.txt

# Настройка config.json (измените download_path на ./downloads)

# Запуск
python -m src.main
```

## Важные файлы

- `config.json` - основная конфигурация приложения
- `docker-compose.yml` - настройки Docker сервиса
- `downloads/` - директория со скачанными релизами
- [CONFIG_EXAMPLES.md](CONFIG_EXAMPLES.md) - примеры конфигураций
- [README.md](README.md) - полная документация
