"""Модуль для загрузки и валидации конфигурации приложения"""
import json
import os
from pathlib import Path
from typing import Any


class Config:
    """Класс для работы с конфигурацией приложения"""
    
    # Обязательные поля конфигурации
    __REQUIRED_FIELDS = [
        'check_interval_seconds',
        'release_page_url',
        'css_selector_link',
        'version_pattern',
        'download_path',
        'filename_template'
    ]
    
    def __init__(self, ConfigPath: str = 'config.json'):
        self._config_path = Path(ConfigPath)
        self._data: dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Загружает конфигурацию из JSON файла и выполняет валидацию"""
        if not self._config_path.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {self._config_path}")
        
        try:
            with open(self._config_path, 'r', encoding='utf-8') as file:
                self._data = json.load(file)
        except json.JSONDecodeError as ex:
            raise ValueError(f"Ошибка парсинга JSON в файле {self._config_path}: {ex}")
        
        self._validate()
    
    def _validate(self) -> None:
        """Валидирует наличие всех обязательных полей"""
        missing_fields = [field for field in self.__REQUIRED_FIELDS if field not in self._data]
        
        if missing_fields:
            raise ValueError(f"В конфигурации отсутствуют обязательные поля: {', '.join(missing_fields)}")
        
        # Валидация типов
        if not isinstance(self._data['check_interval_seconds'], (int, float)) or self._data['check_interval_seconds'] <= 0:
            raise ValueError("check_interval_seconds должен быть положительным числом")
        
        if not isinstance(self._data['release_page_url'], str) or not self._data['release_page_url'].startswith('http'):
            raise ValueError("release_page_url должен быть валидным URL")
    
    @property
    def check_interval_seconds(self) -> int:
        """Интервал проверки новых релизов в секундах"""
        return int(self._data['check_interval_seconds'])
    
    @property
    def release_page_url(self) -> str:
        """URL страницы с релизами"""
        return self._data['release_page_url']
    
    @property
    def css_selector_link(self) -> str:
        """CSS селектор для поиска ссылки на скачивание"""
        return self._data['css_selector_link']
    
    @property
    def css_selector_version(self) -> str:
        """CSS селектор для поиска версии (опционально)"""
        return self._data.get('css_selector_version', '')
    
    @property
    def version_pattern(self) -> str:
        """Regex паттерн для извлечения версии"""
        return self._data['version_pattern']
    
    @property
    def download_path(self) -> str:
        """Путь для сохранения скачанных файлов"""
        return self._data['download_path']
    
    @property
    def filename_template(self) -> str:
        """Шаблон имени файла с плейсхолдером {version}"""
        return self._data['filename_template']
    
    @property
    def user_agent(self) -> str:
        """User-Agent для HTTP запросов"""
        return self._data.get('user_agent', 'DockerReleaseChecker/1.0')
    
    def reload(self) -> None:
        """Перезагружает конфигурацию из файла"""
        self.load()
