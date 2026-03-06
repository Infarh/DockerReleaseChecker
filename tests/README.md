# Тесты Docker Release Checker

## Структура тестов

- **conftest.py** - общие фикстуры для всех тестов
- **test_config.py** - 10 тестов модуля конфигурации
- **test_checker.py** - 15 тестов модуля проверки релизов
- **test_integration.py** - 6 интеграционных тестов

## Быстрый запуск

```bash
# Из корневой директории проекта
pytest

# Или конкретный файл
pytest tests/test_config.py
pytest tests/test_checker.py
pytest tests/test_integration.py
```

## Статистика

- **Всего тестов: 31**
- **Время выполнения: ~1.5 секунды**
- **Покрытие кода: 74%**

## Документация

См. подробную документацию:
- [TESTING.md](../TESTING.md) - руководство по запуску
- [TEST_REPORT.md](../TEST_REPORT.md) - детальный отчет
- [VERIFICATION_REPORT.md](../VERIFICATION_REPORT.md) - финальная верификация
