"""Тесты для модуля config.py"""
import json
import pytest
from pathlib import Path
from src.config import Config


class TestConfig:
    """Тесты класса Config"""
    
    def test_load_valid_config(self, temp_config_file):
        """Тест загрузки валидной конфигурации"""
        config = Config(temp_config_file)
        
        assert config.check_interval_seconds == 60
        assert config.release_page_url == "https://example.com/releases"
        assert config.css_selector_link == "a.download"
        assert config.css_selector_version == "h2"
        assert config.version_pattern == r"(\d+\.\d+\.\d+)"
        assert config.download_path == "/tmp/downloads"
        assert config.filename_template == "test-{version}.exe"
        assert config.user_agent == "TestAgent/1.0"
    
    def test_config_file_not_found(self):
        """Тест обработки отсутствующего файла конфигурации"""
        with pytest.raises(FileNotFoundError) as exc_info:
            Config("nonexistent_config.json")
        
        assert "Файл конфигурации не найден" in str(exc_info.value)
    
    def test_invalid_json(self, invalid_config_file):
        """Тест обработки невалидного JSON"""
        with pytest.raises(ValueError) as exc_info:
            Config(invalid_config_file)
        
        assert "Ошибка парсинга JSON" in str(exc_info.value)
    
    def test_missing_required_fields(self, incomplete_config_file):
        """Тест обработки отсутствующих обязательных полей"""
        with pytest.raises(ValueError) as exc_info:
            Config(incomplete_config_file)
        
        assert "отсутствуют обязательные поля" in str(exc_info.value)
    
    def test_invalid_interval_type(self, tmp_path):
        """Тест валидации типа интервала проверки"""
        config_file = tmp_path / "config.json"
        config_data = {
            "check_interval_seconds": "not_a_number",  # Неправильный тип
            "release_page_url": "https://example.com",
            "css_selector_link": "a",
            "version_pattern": r"(\d+\.\d+\.\d+)",
            "download_path": "/tmp",
            "filename_template": "test-{version}.exe"
        }
        config_file.write_text(json.dumps(config_data), encoding='utf-8')
        
        with pytest.raises(ValueError) as exc_info:
            Config(str(config_file))
        
        assert "check_interval_seconds должен быть положительным числом" in str(exc_info.value)
    
    def test_negative_interval(self, tmp_path):
        """Тест валидации отрицательного интервала"""
        config_file = tmp_path / "config.json"
        config_data = {
            "check_interval_seconds": -10,  # Отрицательное значение
            "release_page_url": "https://example.com",
            "css_selector_link": "a",
            "version_pattern": r"(\d+\.\d+\.\d+)",
            "download_path": "/tmp",
            "filename_template": "test-{version}.exe"
        }
        config_file.write_text(json.dumps(config_data), encoding='utf-8')
        
        with pytest.raises(ValueError) as exc_info:
            Config(str(config_file))
        
        assert "должен быть положительным числом" in str(exc_info.value)
    
    def test_invalid_url(self, tmp_path):
        """Тест валидации невалидного URL"""
        config_file = tmp_path / "config.json"
        config_data = {
            "check_interval_seconds": 60,
            "release_page_url": "not_a_url",  # Невалидный URL
            "css_selector_link": "a",
            "version_pattern": r"(\d+\.\d+\.\d+)",
            "download_path": "/tmp",
            "filename_template": "test-{version}.exe"
        }
        config_file.write_text(json.dumps(config_data), encoding='utf-8')
        
        with pytest.raises(ValueError) as exc_info:
            Config(str(config_file))
        
        assert "должен быть валидным URL" in str(exc_info.value)
    
    def test_reload_config(self, tmp_path):
        """Тест перезагрузки конфигурации"""
        config_file = tmp_path / "config.json"
        
        # Создаем начальную конфигурацию
        initial_config = {
            "check_interval_seconds": 60,
            "release_page_url": "https://example.com",
            "css_selector_link": "a",
            "version_pattern": r"(\d+\.\d+\.\d+)",
            "download_path": "/tmp",
            "filename_template": "test-{version}.exe"
        }
        config_file.write_text(json.dumps(initial_config), encoding='utf-8')
        
        config = Config(str(config_file))
        assert config.check_interval_seconds == 60
        
        # Изменяем конфигурацию
        updated_config = initial_config.copy()
        updated_config["check_interval_seconds"] = 120
        config_file.write_text(json.dumps(updated_config), encoding='utf-8')
        
        # Перезагружаем
        config.reload()
        assert config.check_interval_seconds == 120
    
    def test_optional_css_selector_version(self, tmp_path):
        """Тест опционального параметра css_selector_version"""
        config_file = tmp_path / "config.json"
        config_data = {
            "check_interval_seconds": 60,
            "release_page_url": "https://example.com",
            "css_selector_link": "a",
            "version_pattern": r"(\d+\.\d+\.\d+)",
            "download_path": "/tmp",
            "filename_template": "test-{version}.exe"
            # css_selector_version отсутствует
        }
        config_file.write_text(json.dumps(config_data), encoding='utf-8')
        
        config = Config(str(config_file))
        assert config.css_selector_version == ""  # Должно вернуть пустую строку
    
    def test_default_user_agent(self, tmp_path):
        """Тест дефолтного user-agent"""
        config_file = tmp_path / "config.json"
        config_data = {
            "check_interval_seconds": 60,
            "release_page_url": "https://example.com",
            "css_selector_link": "a",
            "version_pattern": r"(\d+\.\d+\.\d+)",
            "download_path": "/tmp",
            "filename_template": "test-{version}.exe"
            # user_agent отсутствует
        }
        config_file.write_text(json.dumps(config_data), encoding='utf-8')
        
        config = Config(str(config_file))
        assert config.user_agent == "DockerReleaseChecker/1.0"
