"""Модуль для проверки новых релизов Docker Desktop и их скачивания"""
import re
import json
import logging
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from packaging import version

from .config import Config


class ReleaseChecker:
    """Класс для мониторинга и скачивания новых релизов Docker Desktop"""
    
    # Имя файла для хранения времени последней проверки
    _TIMESTAMP_FILE = '.last_check_timestamp.json'
    
    def __init__(self, Config: Config):
        self._config = Config
        self._logger = logging.getLogger(__name__)
        self._session = requests.Session()
        self._session.headers.update({'User-Agent': self._config.user_agent})
        self._timestamp_path = Path(self._config.download_path) / self._TIMESTAMP_FILE
    
    def check_and_download(self) -> None:
        """Основной метод: проверяет наличие нового релиза и скачивает его при необходимости"""
        try:
            # Сохраняем время начала проверки
            self._save_check_timestamp()
            
            # Получаем информацию о релизе с сайта
            latest_version, download_url = self._fetch_latest_release()
            
            if not latest_version or not download_url:
                self._logger.warning("Не удалось найти информацию о релизе на странице")
                return
            
            self._logger.info(f"Найдена версия на сайте: {latest_version}")
            
            # Получаем последнюю локальную версию
            local_version = self._get_local_latest_version()
            
            if local_version:
                self._logger.info(f"Последняя локальная версия: {local_version}")
                
                # Сравниваем версии
                if self._compare_versions(latest_version, local_version) <= 0:
                    self._logger.info("Локальная версия актуальна, скачивание не требуется")
                    return
            else:
                self._logger.info("Локальные версии не найдены")
            
            # Скачиваем новый релиз
            self._logger.info(f"Доступна новая версия {latest_version}, начинаю скачивание...")
            self._download_release(latest_version, download_url)
            self._logger.info(f"Релиз {latest_version} успешно скачан")
            
        except Exception as ex:
            self._logger.error(f"Ошибка при проверке релиза: {ex}", exc_info=True)
    
    def get_seconds_since_last_check(self) -> Optional[float]:
        """Возвращает количество секунд с момента последней проверки или None, если это первая проверка"""
        last_check_time = self._load_check_timestamp()
        if last_check_time is None:
            return None
        return time.time() - last_check_time
    
    def _save_check_timestamp(self) -> None:
        """Сохраняет время текущей проверки в файл"""
        try:
            timestamp_dir = self._timestamp_path.parent
            timestamp_dir.mkdir(parents=True, exist_ok=True)
            
            data = {'last_check_time': time.time()}
            with open(self._timestamp_path, 'w', encoding='utf-8') as file:
                json.dump(data, file)
        except Exception as ex:
            self._logger.warning(f"Не удалось сохранить timestamp: {ex}")
    
    def _load_check_timestamp(self) -> Optional[float]:
        """Загружает время последней проверки из файла"""
        try:
            if not self._timestamp_path.exists():
                return None
            
            with open(self._timestamp_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data.get('last_check_time')
        except Exception as ex:
            self._logger.warning(f"Не удалось загрузить timestamp: {ex}")
            return None
    
    def _fetch_latest_release(self) -> tuple[Optional[str], Optional[str]]:
        """Получает информацию о последнем релизе со страницы"""
        try:
            response = self._session.get(self._config.release_page_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Ищем наиболее релевантную ссылку на Windows-инсталлятор
            link_element = self._find_best_download_link(soup)
            
            if not link_element:
                self._logger.warning(f"Не найден элемент по селектору: {self._config.css_selector_link}")
                return None, None
            
            download_url = link_element.get('href')
            if not download_url:
                self._logger.warning("Найденный элемент не содержит атрибут href")
                return None, None
            
            # Преобразуем относительный URL в абсолютный
            download_url = urljoin(self._config.release_page_url, download_url)
            
            # Извлекаем версию
            version_str = self._extract_version_from_page(soup, link_element)
            
            if not version_str:
                self._logger.warning("Не удалось извлечь версию из страницы")
                return None, None
            
            return version_str, download_url
            
        except requests.RequestException as ex:
            self._logger.error(f"Ошибка при получении страницы релиза: {ex}")
            return None, None

    def _find_best_download_link(self, Soup: BeautifulSoup):
        """Находит лучшую ссылку на установщик Windows среди всех совпадений"""
        elements = Soup.select(self._config.css_selector_link)

        if elements:
            best = max(elements, key=self._score_download_link)
            if self._score_download_link(best) > 0:
                return best

        # Fallback: если селектор оказался слишком широким/неудачным, ищем по всем ссылкам
        all_links = Soup.find_all('a', href=True)
        if not all_links:
            return None

        best = max(all_links, key=self._score_download_link)
        return best if self._score_download_link(best) > 0 else None

    def _score_download_link(self, LinkElement) -> int:
        """Оценивает ссылку: чем выше балл, тем вероятнее что это нужный installer"""
        href = (LinkElement.get('href') or '').strip()
        text = LinkElement.get_text(strip=True).lower()
        href_lower = href.lower()

        score = 0

        # Максимально приоритетная ссылка: официальный Windows installer
        if 'desktop.docker.com/win/' in href_lower and 'docker%20desktop%20installer.exe' in href_lower:
            score += 100

        # Альтернатива: любая exe-ссылка на windows
        if '.exe' in href_lower:
            score += 60

        if '/win/' in href_lower or 'windows' in href_lower:
            score += 30

        # Снижаем приоритет ссылок документации
        if 'docs.docker.com' in href_lower:
            score -= 40

        if 'windows' in text:
            score += 10

        return score
    
    def _extract_version_from_page(self, Soup: BeautifulSoup, LinkElement) -> Optional[str]:
        """Извлекает версию из страницы используя regex паттерн"""
        pattern = re.compile(self._config.version_pattern)
        
        # Пытаемся извлечь версию из различных источников
        sources = [
            LinkElement.get('href', ''),
            LinkElement.get_text(strip=True),
        ]
        
        # Если указан селектор для версии, добавляем его результат
        if self._config.css_selector_version:
            version_element = Soup.select_one(self._config.css_selector_version)
            if version_element:
                sources.append(version_element.get_text(strip=True))
        
        # Пытаемся найти версию в каждом источнике
        for source in sources:
            match = pattern.search(source)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        
        return None
    
    def _get_local_latest_version(self) -> Optional[str]:
        """Сканирует каталог загрузок и возвращает последнюю версию"""
        download_dir = Path(self._config.download_path)
        
        if not download_dir.exists():
            return None
        
        # Ищем все файлы, соответствующие паттерну
        pattern = re.compile(self._config.version_pattern)
        versions = []
        
        for file_path in download_dir.iterdir():
            if file_path.is_file():
                match = pattern.search(file_path.name)
                if match:
                    version_str = match.group(1) if match.groups() else match.group(0)
                    versions.append(version_str)
        
        if not versions:
            return None
        
        # Сортируем версии и возвращаем последнюю
        versions.sort(key=lambda v: version.parse(v), reverse=True)
        return versions[0]
    
    def _compare_versions(self, Version1: str, Version2: str) -> int:
        """Сравнивает две версии. Возвращает: >0 если v1 > v2, 0 если равны, <0 если v1 < v2"""
        try:
            v1 = version.parse(Version1)
            v2 = version.parse(Version2)
            
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
            else:
                return 0
        except Exception as ex:
            self._logger.warning(f"Ошибка сравнения версий {Version1} и {Version2}: {ex}")
            return 0
    
    def _download_release(self, Version: str, Url: str) -> None:
        """Скачивает файл релиза"""
        download_dir = Path(self._config.download_path)
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # Формируем имя файла
        filename = self._config.filename_template.format(version=Version)
        file_path = download_dir / filename
        
        # Скачиваем файл с отображением прогресса
        self._logger.info(f"Скачивание из: {Url}")
        self._logger.info(f"Сохранение в: {file_path}")
        
        try:
            response = self._session.get(Url, stream=True, timeout=60)
            response.raise_for_status()

            content_type = (response.headers.get('content-type') or '').lower()
            if 'text/html' in content_type:
                raise ValueError(f"Ожидался бинарный файл, но получен HTML (Content-Type: {content_type})")
            
            total_size = int(response.headers.get('content-length', 0))
            if total_size > 0:
                self._logger.info(f"Размер файла: {total_size // (1024*1024)} МБ")
            
            downloaded_size = 0
            chunk_size = 8192

            chunk_iterator = response.iter_content(chunk_size=chunk_size)
            first_chunk = b''
            for chunk in chunk_iterator:
                if chunk:
                    first_chunk = chunk
                    break

            if not first_chunk:
                raise ValueError("Скачанный файл пуст")

            # PE-файл Windows должен начинаться с сигнатуры MZ
            if not first_chunk.startswith(b'MZ'):
                raise ValueError("Скачанный файл не похож на Windows PE-инсталлятор (нет сигнатуры MZ)")

            with open(file_path, 'wb') as file:
                file.write(first_chunk)
                downloaded_size += len(first_chunk)

                for chunk in chunk_iterator:
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Логируем прогресс каждые 10 МБ
                        if total_size > 0 and downloaded_size % (10 * 1024 * 1024) < chunk_size:
                            progress = (downloaded_size / total_size) * 100
                            self._logger.info(f"Прогресс: {progress:.1f}% ({downloaded_size // (1024*1024)} МБ / {total_size // (1024*1024)} МБ)")
            
            # Проверяем целостность загрузки
            if total_size > 0 and downloaded_size != total_size:
                raise ValueError(f"Размер загруженного файла ({downloaded_size} байт) не совпадает с ожидаемым ({total_size} байт)")
            
            self._logger.info(f"Файл успешно сохранен: {file_path} ({downloaded_size // (1024*1024)} МБ)")
            
        except Exception as ex:
            self._logger.error(f"Ошибка при скачивании файла: {ex}")
            # Удаляем битый/неполный файл при любой ошибке
            if file_path.exists():
                try:
                    file_path.unlink()
                    self._logger.info(f"Битый файл удалён: {file_path}")
                except Exception as unlink_ex:
                    self._logger.warning(f"Не удалось удалить битый файл {file_path}: {unlink_ex}")
            raise
