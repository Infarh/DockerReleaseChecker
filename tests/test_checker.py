"""Тесты для модуля checker.py"""
import json
import pytest
import responses
from pathlib import Path
from unittest.mock import Mock, patch
from src.config import Config
from src.checker import ReleaseChecker


class TestReleaseChecker:
    """Тесты класса ReleaseChecker"""
    
    @pytest.fixture
    def mock_config(self, tmp_path):
        """Создает моковую конфигурацию для тестов"""
        config_file = tmp_path / "config.json"
        download_dir = tmp_path / "downloads"
        download_dir.mkdir()
        
        config_data = {
            "check_interval_seconds": 60,
            "release_page_url": "https://example.com/releases",
            "css_selector_link": "a.download",
            "css_selector_version": "h2",
            "version_pattern": r"(\d+\.\d+\.\d+)",
            "download_path": str(download_dir),
            "filename_template": "app-{version}-windows.exe",
            "user_agent": "TestAgent/1.0"
        }
        config_file.write_text(json.dumps(config_data), encoding='utf-8')
        
        return Config(str(config_file))
    
    @responses.activate
    def test_fetch_latest_release_success(self, mock_config, sample_html_page):
        """Тест успешного получения информации о релизе"""
        responses.add(
            responses.GET,
            "https://example.com/releases",
            body=sample_html_page,
            status=200
        )
        
        checker = ReleaseChecker(mock_config)
        version, url = checker._fetch_latest_release()
        
        assert version == "4.28.0"
        assert url == "https://example.com/downloads/app-4.28.0-windows.exe"
    
    @responses.activate
    def test_fetch_latest_release_network_error(self, mock_config):
        """Тест обработки сетевой ошибки"""
        responses.add(
            responses.GET,
            "https://example.com/releases",
            body="Server Error",
            status=500
        )
        
        checker = ReleaseChecker(mock_config)
        version, url = checker._fetch_latest_release()
        
        assert version is None
        assert url is None
    
    @responses.activate
    def test_fetch_latest_release_no_link_found(self, mock_config):
        """Тест когда CSS селектор не находит элемент"""
        html = "<html><body><p>No links here</p></body></html>"
        responses.add(
            responses.GET,
            "https://example.com/releases",
            body=html,
            status=200
        )
        
        checker = ReleaseChecker(mock_config)
        version, url = checker._fetch_latest_release()
        
        assert version is None
        assert url is None
    
    def test_extract_version_from_link_href(self, mock_config):
        """Тест извлечения версии из href ссылки"""
        from bs4 import BeautifulSoup
        
        html = '<a href="/download/app-4.28.0-windows.exe">Download</a>'
        soup = BeautifulSoup(html, 'lxml')
        link = soup.find('a')
        
        checker = ReleaseChecker(mock_config)
        version = checker._extract_version_from_page(soup, link)
        
        assert version == "4.28.0"
    
    def test_extract_version_from_link_text(self, mock_config):
        """Тест извлечения версии из текста ссылки"""
        from bs4 import BeautifulSoup
        
        html = '<a href="/download">Version 4.28.0</a>'
        soup = BeautifulSoup(html, 'lxml')
        link = soup.find('a')
        
        checker = ReleaseChecker(mock_config)
        version = checker._extract_version_from_page(soup, link)
        
        assert version == "4.28.0"
    
    def test_extract_version_from_selector(self, mock_config):
        """Тест извлечения версии через CSS селектор"""
        from bs4 import BeautifulSoup
        
        html = '<h2>Version 4.28.0</h2><a href="/download">Download</a>'
        soup = BeautifulSoup(html, 'lxml')
        link = soup.find('a')
        
        checker = ReleaseChecker(mock_config)
        version = checker._extract_version_from_page(soup, link)
        
        assert version == "4.28.0"
    
    def test_get_local_latest_version_empty_dir(self, mock_config):
        """Тест получения локальной версии из пустой директории"""
        checker = ReleaseChecker(mock_config)
        version = checker._get_local_latest_version()
        
        assert version is None
    
    def test_get_local_latest_version_with_files(self, mock_config):
        """Тест получения последней локальной версии"""
        download_dir = Path(mock_config.download_path)
        
        # Создаем файлы с разными версиями
        (download_dir / "app-4.25.0-windows.exe").touch()
        (download_dir / "app-4.28.0-windows.exe").touch()
        (download_dir / "app-4.27.0-windows.exe").touch()
        
        checker = ReleaseChecker(mock_config)
        version = checker._get_local_latest_version()
        
        assert version == "4.28.0"
    
    def test_compare_versions_greater(self, mock_config):
        """Тест сравнения версий: новая > старая"""
        checker = ReleaseChecker(mock_config)
        result = checker._compare_versions("4.28.0", "4.27.0")
        
        assert result > 0
    
    def test_compare_versions_equal(self, mock_config):
        """Тест сравнения версий: равные версии"""
        checker = ReleaseChecker(mock_config)
        result = checker._compare_versions("4.28.0", "4.28.0")
        
        assert result == 0
    
    def test_compare_versions_less(self, mock_config):
        """Тест сравнения версий: старая < новая"""
        checker = ReleaseChecker(mock_config)
        result = checker._compare_versions("4.27.0", "4.28.0")
        
        assert result < 0
    
    @responses.activate
    def test_download_release_success(self, mock_config):
        """Тест успешного скачивания файла"""
        file_content = b"fake installer content"
        responses.add(
            responses.GET,
            "https://example.com/downloads/app-4.28.0-windows.exe",
            body=file_content,
            status=200,
            headers={"content-length": str(len(file_content))}
        )
        
        checker = ReleaseChecker(mock_config)
        checker._download_release("4.28.0", "https://example.com/downloads/app-4.28.0-windows.exe")
        
        expected_file = Path(mock_config.download_path) / "app-4.28.0-windows.exe"
        assert expected_file.exists()
        assert expected_file.read_bytes() == file_content
    
    @responses.activate
    def test_download_release_network_error(self, mock_config):
        """Тест обработки ошибки при скачивании"""
        responses.add(
            responses.GET,
            "https://example.com/downloads/app-4.28.0-windows.exe",
            body="Server Error",
            status=500
        )
        
        checker = ReleaseChecker(mock_config)
        
        with pytest.raises(Exception):
            checker._download_release("4.28.0", "https://example.com/downloads/app-4.28.0-windows.exe")
        
        # Проверяем, что файл не был создан или был удален
        expected_file = Path(mock_config.download_path) / "app-4.28.0-windows.exe"
        assert not expected_file.exists()
    
    @responses.activate
    def test_check_and_download_new_version(self, mock_config, sample_html_page):
        """Тест полного цикла: проверка и скачивание новой версии"""
        # Мокируем страницу релизов
        responses.add(
            responses.GET,
            "https://example.com/releases",
            body=sample_html_page,
            status=200
        )
        
        # Мокируем скачивание файла
        responses.add(
            responses.GET,
            "https://example.com/downloads/app-4.28.0-windows.exe",
            body=b"fake installer",
            status=200,
            headers={"content-length": "14"}
        )
        
        checker = ReleaseChecker(mock_config)
        checker.check_and_download()
        
        # Проверяем, что файл был скачан
        expected_file = Path(mock_config.download_path) / "app-4.28.0-windows.exe"
        assert expected_file.exists()
    
    @responses.activate
    def test_check_and_download_no_new_version(self, mock_config, sample_html_page):
        """Тест когда локальная версия уже актуальна"""
        # Создаем локальный файл с текущей версией
        download_dir = Path(mock_config.download_path)
        (download_dir / "app-4.28.0-windows.exe").touch()
        
        # Мокируем страницу релизов
        responses.add(
            responses.GET,
            "https://example.com/releases",
            body=sample_html_page,
            status=200
        )
        
        checker = ReleaseChecker(mock_config)
        checker.check_and_download()
        
        # Проверяем, что новый файл не был создан
        files = list(download_dir.glob("*.exe"))
        assert len(files) == 1  # Только один файл - изначально созданный
