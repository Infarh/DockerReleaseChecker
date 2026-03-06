"""Фикстуры pytest для тестирования"""
import json
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def temp_config_file():
    """Создает временный файл конфигурации для тестов"""
    config_data = {
        "check_interval_seconds": 60,
        "release_page_url": "https://example.com/releases",
        "css_selector_link": "a.download",
        "css_selector_version": "h2",
        "version_pattern": r"(\d+\.\d+\.\d+)",
        "download_path": "/tmp/downloads",
        "filename_template": "test-{version}.exe",
        "user_agent": "TestAgent/1.0"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
        json.dump(config_data, temp_file)
        temp_path = temp_file.name
    
    yield temp_path
    
    # Очистка после теста
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_download_dir(tmp_path):
    """Создает временную директорию для скачивания"""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    return download_dir


@pytest.fixture
def sample_html_page():
    """Возвращает пример HTML страницы с релизом"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Releases</title></head>
    <body>
        <h1>Downloads</h1>
        <div class="release">
            <h2>Version 4.28.0</h2>
            <a class="download" href="https://example.com/downloads/app-4.28.0-windows.exe">
                Download for Windows
            </a>
        </div>
        <div class="release">
            <h2>Version 4.27.0</h2>
            <a class="download" href="https://example.com/downloads/app-4.27.0-windows.exe">
                Download for Windows
            </a>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def invalid_config_file():
    """Создает невалидный файл конфигурации"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
        temp_file.write("{ invalid json }")
        temp_path = temp_file.name
    
    yield temp_path
    
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def incomplete_config_file():
    """Создает конфигурацию с отсутствующими обязательными полями"""
    config_data = {
        "check_interval_seconds": 60,
        "release_page_url": "https://example.com/releases"
        # Отсутствуют обязательные поля
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
        json.dump(config_data, temp_file)
        temp_path = temp_file.name
    
    yield temp_path
    
    Path(temp_path).unlink(missing_ok=True)
