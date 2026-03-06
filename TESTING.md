# Скрипт для запуска тестов Docker Release Checker

## Установка зависимостей для тестирования

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Запуск всех тестов

```bash
pytest
```

## Запуск с подробным выводом

```bash
pytest -v
```

## Запуск конкретного файла тестов

```bash
pytest tests/test_config.py
pytest tests/test_checker.py
pytest tests/test_integration.py
```

## Запуск конкретного теста

```bash
pytest tests/test_config.py::TestConfig::test_load_valid_config
```

## Запуск с покрытием кода

```bash
pytest --cov=src --cov-report=html
```

После выполнения откройте `htmlcov/index.html` в браузере для просмотра отчета о покрытии.

## Запуск только быстрых тестов (без интеграционных)

```bash
pytest tests/test_config.py tests/test_checker.py
```

## Запуск только интеграционных тестов

```bash
pytest tests/test_integration.py
```

## Запуск в режиме отладки (остановка на первой ошибке)

```bash
pytest -x
```

## Запуск с выводом принтов

```bash
pytest -s
```

## Проверка покрытия кода

```bash
pytest --cov=src --cov-report=term-missing
```

Это покажет какие строки кода не покрыты тестами.

## Генерация HTML отчета о покрытии

```bash
pytest --cov=src --cov-report=html
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html  # Linux
```

## Непрерывное тестирование (автоматический перезапуск при изменении файлов)

Установите pytest-watch:
```bash
pip install pytest-watch
```

Запустите:
```bash
ptw
```

## Структура тестов

- `tests/test_config.py` - тесты модуля конфигурации
- `tests/test_checker.py` - тесты модуля проверки релизов
- `tests/test_integration.py` - интеграционные тесты
- `tests/conftest.py` - общие фикстуры для всех тестов

## Категории тестов

- **Unit tests** (модульные) - тестируют отдельные функции и методы
- **Integration tests** (интеграционные) - тестируют взаимодействие между компонентами

## Минимальный процент покрытия

Проект настроен на минимум 80% покрытия кода тестами.
