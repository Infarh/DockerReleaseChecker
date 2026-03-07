"""Health check скрипт для мониторинга работоспособности контейнера"""
import sys
import json
import time
from pathlib import Path


def check_health() -> bool:
    """Проверяет работоспособность приложения"""
    try:
        # Путь к файлу с timestamp последней проверки
        timestamp_file = Path('/downloads/.last_check_timestamp.json')
        
        # Если файл не существует, значит ещё не было ни одной проверки
        # Это нормально при первом запуске
        if not timestamp_file.exists():
            print("OK: Приложение запущено, ожидается первая проверка")
            return True
        
        # Читаем timestamp
        with open(timestamp_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            last_check_time = data.get('last_check_time')
        
        if last_check_time is None:
            print("WARN: Файл timestamp существует, но не содержит данных")
            return False
        
        # Вычисляем время с последней проверки
        elapsed_seconds = time.time() - last_check_time
        elapsed_minutes = elapsed_seconds / 60
        
        # Читаем конфигурацию для получения интервала проверки
        config_file = Path('/app/config.json')
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as file:
                config = json.load(file)
                check_interval = config.get('check_interval_seconds', 3600)
        else:
            # Используем дефолтный интервал если конфиг недоступен
            check_interval = 3600
        
        # Проверяем, что последняя проверка была не слишком давно
        # Допускаем задержку до 3x интервала (на случай проблем с сетью)
        max_allowed_delay = check_interval * 3
        
        if elapsed_seconds > max_allowed_delay:
            print(f"FAIL: Последняя проверка была {elapsed_minutes:.1f} минут назад "
                  f"(допустимо до {max_allowed_delay/60:.1f} минут)")
            return False
        
        print(f"OK: Последняя проверка была {elapsed_minutes:.1f} минут назад")
        return True
        
    except json.JSONDecodeError as ex:
        print(f"FAIL: Ошибка парсинга JSON: {ex}")
        return False
    except Exception as ex:
        print(f"FAIL: Неожиданная ошибка: {ex}")
        return False


if __name__ == '__main__':
    is_healthy = check_health()
    sys.exit(0 if is_healthy else 1)
