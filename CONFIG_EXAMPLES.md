# Пример конфигурации для мониторинга релизов

## Важно: Настройка CSS селекторов

Страница https://docs.docker.com/desktop/release-notes/ содержит информацию о релизах, но **не содержит прямых ссылок на скачивание установщиков**.

Для реального использования необходимо:

### Вариант 1: Использовать страницу скачивания Docker Desktop

```json
{
  "check_interval_seconds": 3600,
  "release_page_url": "https://docs.docker.com/desktop/install/windows-install/",
  "css_selector_link": "a.button[href*='docker.com'][href*='win']",
  "css_selector_version": "h1",
  "version_pattern": "(\\d+\\.\\d+\\.\\d+)",
  "download_path": "/downloads",
  "filename_template": "DockerDesktop-{version}-windows.exe",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

### Вариант 2: Использовать GitHub Releases (если Docker публикует там)

```json
{
  "check_interval_seconds": 3600,
  "release_page_url": "https://github.com/docker/desktop/releases/latest",
  "css_selector_link": "a[href$='.exe']",
  "version_pattern": "v?(\\d+\\.\\d+\\.\\d+)",
  "download_path": "/downloads",
  "filename_template": "DockerDesktop-{version}-windows.exe",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

### Вариант 3: Прямой URL на CDN Docker

Если вы знаете прямой URL на файл релиза Docker Desktop:

```json
{
  "check_interval_seconds": 3600,
  "release_page_url": "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe",
  "css_selector_link": "body",
  "version_pattern": "(\\d+\\.\\d+\\.\\d+)",
  "download_path": "/downloads",
  "filename_template": "DockerDesktop-latest-windows.exe",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

## Как найти правильные селекторы

1. **Откройте страницу релизов в браузере**
2. **Нажмите F12** для открытия DevTools
3. **Найдите элемент с ссылкой на скачивание:**
   - Используйте инспектор элементов (иконка стрелки в DevTools)
   - Кликните на кнопку/ссылку скачивания
4. **Скопируйте CSS селектор:**
   - Правый клик на элементе в DevTools
   - Copy → Copy selector
5. **Протестируйте селектор:**
   - В консоли DevTools выполните: `document.querySelector('ваш_селектор')`
   - Убедитесь, что возвращается нужный элемент

## Тестовый пример с публичным API

Для тестирования логики приложения можно использовать GitHub Releases любого проекта.

Пример с Python:

```json
{
  "check_interval_seconds": 300,
  "release_page_url": "https://www.python.org/downloads/windows/",
  "css_selector_link": "a[href*='amd64.exe'][href*='python-3']",
  "css_selector_version": "h1",
  "version_pattern": "(\\d+\\.\\d+\\.\\d+)",
  "download_path": "./downloads",
  "filename_template": "python-{version}-amd64.exe",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

## Отладка

Для проверки что находит CSS селектор, можно добавить логирование в `src/checker.py`:

```python
# После строки: link_element = soup.select_one(self._config.css_selector_link)
self._logger.info(f"Найденный элемент: {link_element}")
self._logger.info(f"href: {link_element.get('href') if link_element else 'None'}")
self._logger.info(f"text: {link_element.get_text(strip=True) if link_element else 'None'}")
```

Это поможет увидеть что именно находит селектор и скорректировать его.
