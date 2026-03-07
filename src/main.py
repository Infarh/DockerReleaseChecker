"""Точка входа приложения Docker Release Checker"""
import logging
import sys
import time
from pathlib import Path

from src.config import Config
from src.checker import ReleaseChecker


def setup_logging() -> None:
    """Настраивает логирование в консоль"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def main() -> None:
    """Главная функция приложения"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Docker Release Checker - Запуск приложения")
    logger.info("=" * 60)
    
    config_path = 'config.json'
    
    # Проверяем наличие файла конфигурации
    if not Path(config_path).exists():
        logger.error(f"Файл конфигурации не найден: {config_path}")
        sys.exit(1)
    
    while True:
        try:
            # Загружаем/перезагружаем конфигурацию
            logger.info("Загрузка конфигурации...")
            config = Config(config_path)
            
            logger.info(f"Конфигурация загружена:")
            logger.info(f"  - URL релиза: {config.release_page_url}")
            logger.info(f"  - Интервал проверки: {config.check_interval_seconds} сек ({config.check_interval_seconds // 60} мин)")
            logger.info(f"  - Путь сохранения: {config.download_path}")
            logger.info(f"  - CSS селектор: {config.css_selector_link}")
            
            # Создаем чекер
            checker = ReleaseChecker(config)
            
            # Проверяем, сколько времени прошло с последней проверки
            seconds_since_last = checker.get_seconds_since_last_check()
            if seconds_since_last is not None:
                logger.info(f"Время с последней проверки: {int(seconds_since_last)} сек ({int(seconds_since_last // 60)} мин)")
                
                # Если прошло слишком много времени (например, после перезагрузки)
                if seconds_since_last > config.check_interval_seconds * 1.5:
                    logger.warning(f"Пропущен интервал проверки! Должно быть {config.check_interval_seconds} сек, прошло {int(seconds_since_last)} сек")
                else:
                    # Вычисляем оставшееся время до следующей проверки
                    remaining_time = config.check_interval_seconds - seconds_since_last
                    if remaining_time > 0:
                        logger.info(f"До следующей проверки осталось {int(remaining_time)} сек. Ожидание...")
                        time.sleep(remaining_time)
            
            logger.info("-" * 60)
            logger.info("Начало проверки новых релизов...")
            
            checker.check_and_download()
            
            logger.info("-" * 60)
            logger.info(f"Проверка завершена. Следующая проверка через {config.check_interval_seconds} секунд")
            logger.info(f"Время следующей проверки: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + config.check_interval_seconds))}")
            
            # Ожидаем указанный интервал
            time.sleep(config.check_interval_seconds)
            
        except KeyboardInterrupt:
            logger.info("\nПолучен сигнал остановки (Ctrl+C)")
            logger.info("Завершение работы приложения...")
            break
            
        except Exception as ex:
            logger.error(f"Критическая ошибка: {ex}", exc_info=True)
            logger.info("Повтор через 60 секунд...")
            time.sleep(60)
    
    logger.info("Приложение остановлено")


if __name__ == '__main__':
    main()
