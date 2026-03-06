"""Интеграционные тесты для всего приложения"""
import json
import pytest
import responses
from pathlib import Path
from src.config import Config
from src.checker import ReleaseChecker


class TestIntegration:
    """Интеграционные тесты полного цикла работы"""
    
    @pytest.fixture
    def setup_environment(self, tmp_path):
        """Подготовка окружения для интеграционного теста"""
        # Создаем структуру директорий
        download_dir = tmp_path / "downloads"
        download_dir.mkdir()
        
        config_file = tmp_path / "config.json"
        
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
        
        return {
            "config_file": str(config_file),
            "download_dir": download_dir
        }
    
    @responses.activate
    def test_full_workflow_first_download(self, setup_environment):
        """Тест полного рабочего процесса: первое скачивание"""
        env = setup_environment
        
        # Мокируем HTML страницу с релизами
        html_page = """
        <html>
        <body>
            <h2>Version 5.0.0</h2>
            <a class="download" href="/downloads/app-5.0.0-windows.exe">Download</a>
        </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            "https://example.com/releases",
            body=html_page,
            status=200
        )
        
        # Мокируем скачивание файла
        file_content = b"fake installer content for version 5.0.0"
        responses.add(
            responses.GET,
            "https://example.com/downloads/app-5.0.0-windows.exe",
            body=file_content,
            status=200,
            headers={"content-length": str(len(file_content))}
        )
        
        # Загружаем конфигурацию и запускаем проверку
        config = Config(env["config_file"])
        checker = ReleaseChecker(config)
        checker.check_and_download()
        
        # Проверяем результаты
        expected_file = env["download_dir"] / "app-5.0.0-windows.exe"
        assert expected_file.exists()
        assert expected_file.read_bytes() == file_content
    
    @responses.activate
    def test_full_workflow_upgrade(self, setup_environment):
        """Тест полного рабочего процесса: обновление существующей версии"""
        env = setup_environment
        
        # Создаем файл старой версии
        old_file = env["download_dir"] / "app-4.0.0-windows.exe"
        old_file.write_bytes(b"old version")
        
        # Мокируем HTML страницу с новой версией
        html_page = """
        <html>
        <body>
            <h2>Version 5.0.0</h2>
            <a class="download" href="/downloads/app-5.0.0-windows.exe">Download</a>
        </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            "https://example.com/releases",
            body=html_page,
            status=200
        )
        
        # Мокируем скачивание нового файла
        new_content = b"new version 5.0.0"
        responses.add(
            responses.GET,
            "https://example.com/downloads/app-5.0.0-windows.exe",
            body=new_content,
            status=200,
            headers={"content-length": str(len(new_content))}
        )
        
        # Запускаем проверку
        config = Config(env["config_file"])
        checker = ReleaseChecker(config)
        checker.check_and_download()
        
        # Проверяем, что новый файл появился
        new_file = env["download_dir"] / "app-5.0.0-windows.exe"
        assert new_file.exists()
        assert new_file.read_bytes() == new_content
        
        # Старый файл все еще существует
        assert old_file.exists()
    
    @responses.activate
    def test_full_workflow_no_update_needed(self, setup_environment):
        """Тест когда обновление не требуется"""
        env = setup_environment
        
        # Создаем файл текущей версии
        current_file = env["download_dir"] / "app-5.0.0-windows.exe"
        current_file.write_bytes(b"current version")
        original_mtime = current_file.stat().st_mtime
        
        # Мокируем HTML страницу с той же версией
        html_page = """
        <html>
        <body>
            <h2>Version 5.0.0</h2>
            <a class="download" href="/downloads/app-5.0.0-windows.exe">Download</a>
        </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            "https://example.com/releases",
            body=html_page,
            status=200
        )
        
        # Запускаем проверку (скачивание не должно произойти)
        config = Config(env["config_file"])
        checker = ReleaseChecker(config)
        checker.check_and_download()
        
        # Проверяем, что файл не был изменен
        assert current_file.exists()
        assert current_file.stat().st_mtime == original_mtime
        
        # Проверяем, что количество файлов не изменилось
        files = list(env["download_dir"].glob("*.exe"))
        assert len(files) == 1
    
    @responses.activate
    def test_config_reload_between_checks(self, setup_environment):
        """Тест перезагрузки конфигурации между проверками"""
        env = setup_environment
        
        # Первая конфигурация
        config = Config(env["config_file"])
        assert config.check_interval_seconds == 60
        
        # Изменяем конфигурацию на диске
        config_data = json.loads(Path(env["config_file"]).read_text())
        config_data["check_interval_seconds"] = 120
        Path(env["config_file"]).write_text(json.dumps(config_data), encoding='utf-8')
        
        # Перезагружаем
        config.reload()
        assert config.check_interval_seconds == 120
    
    @responses.activate
    def test_multiple_versions_selection(self, setup_environment):
        """Тест выбора последней версии из нескольких"""
        env = setup_environment
        
        # Создаем несколько файлов разных версий
        (env["download_dir"] / "app-3.0.0-windows.exe").touch()
        (env["download_dir"] / "app-4.5.0-windows.exe").touch()
        (env["download_dir"] / "app-4.0.0-windows.exe").touch()
        
        # Мокируем страницу с еще более новой версией
        html_page = """
        <html>
        <body>
            <h2>Version 5.0.0</h2>
            <a class="download" href="/downloads/app-5.0.0-windows.exe">Download</a>
        </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            "https://example.com/releases",
            body=html_page,
            status=200
        )
        
        responses.add(
            responses.GET,
            "https://example.com/downloads/app-5.0.0-windows.exe",
            body=b"version 5.0.0",
            status=200,
            headers={"content-length": "13"}
        )
        
        # Запускаем проверку
        config = Config(env["config_file"])
        checker = ReleaseChecker(config)
        
        # Проверяем, что нашлась правильная локальная версия (4.5.0)
        local_version = checker._get_local_latest_version()
        assert local_version == "4.5.0"
        
        # Запускаем полную проверку
        checker.check_and_download()
        
        # Проверяем, что новая версия была скачана
        new_file = env["download_dir"] / "app-5.0.0-windows.exe"
        assert new_file.exists()
        
        # Все файлы остались на месте
        files = list(env["download_dir"].glob("*.exe"))
        assert len(files) == 4
    
    def test_error_recovery(self, setup_environment):
        """Тест обработки ошибок и восстановления"""
        env = setup_environment
        
        # Загружаем конфигурацию
        config = Config(env["config_file"])
        checker = ReleaseChecker(config)
        
        # Симулируем проверку без моков (должна обработать ошибку)
        # Не должно выбросить исключение, только залогировать
        checker.check_and_download()
        
        # Проверяем, что ничего не было скачано
        files = list(env["download_dir"].glob("*.exe"))
        assert len(files) == 0
