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
            
            # Создаем чекер и запускаем проверку
            checker = ReleaseChecker(config)
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
