"""Тесты для health check скрипта"""
import json
import time
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from src import healthcheck


def test_healthcheck_no_timestamp_file(tmp_path):
    """Тест: при отсутствии файла timestamp health check проходит (первый запуск)"""
    timestamp_file = tmp_path / '.last_check_timestamp.json'
    
    with patch('src.healthcheck.Path') as mock_path:
        mock_path.return_value.exists.return_value = False
        result = healthcheck.check_health()
    
    assert result is True


def test_healthcheck_recent_check(tmp_path):
    """Тест: при недавней проверке health check проходит"""
    timestamp_file = tmp_path / '.last_check_timestamp.json'
    config_file = tmp_path / 'config.json'
    
    # Создаем timestamp 5 минут назад
    timestamp_data = {'last_check_time': time.time() - 300}
    timestamp_file.write_text(json.dumps(timestamp_data), encoding='utf-8')
    
    # Создаем конфиг с интервалом 1 час
    config_data = {'check_interval_seconds': 3600}
    config_file.write_text(json.dumps(config_data), encoding='utf-8')
    
    with patch('src.healthcheck.Path') as mock_path:
        def path_side_effect(path_str):
            if '.last_check_timestamp.json' in path_str:
                return timestamp_file
            elif 'config.json' in path_str:
                return config_file
            return Path(path_str)
        
        mock_path.side_effect = path_side_effect
        result = healthcheck.check_health()
    
    assert result is True


def test_healthcheck_old_check_within_threshold(tmp_path):
    """Тест: проверка 2 часа назад при интервале 1 час - ещё в пределах нормы (3x интервал)"""
    timestamp_file = tmp_path / '.last_check_timestamp.json'
    config_file = tmp_path / 'config.json'
    
    # Создаем timestamp 2 часа назад
    timestamp_data = {'last_check_time': time.time() - 7200}
    timestamp_file.write_text(json.dumps(timestamp_data), encoding='utf-8')
    
    # Создаем конфиг с интервалом 1 час
    config_data = {'check_interval_seconds': 3600}
    config_file.write_text(json.dumps(config_data), encoding='utf-8')
    
    with patch('src.healthcheck.Path') as mock_path:
        def path_side_effect(path_str):
            if '.last_check_timestamp.json' in path_str:
                return timestamp_file
            elif 'config.json' in path_str:
                return config_file
            return Path(path_str)
        
        mock_path.side_effect = path_side_effect
        result = healthcheck.check_health()
    
    assert result is True


def test_healthcheck_old_check_exceeds_threshold(tmp_path):
    """Тест: проверка 4 часа назад при интервале 1 час - превышен порог (3x интервал)"""
    timestamp_file = tmp_path / '.last_check_timestamp.json'
    config_file = tmp_path / 'config.json'
    
    # Создаем timestamp 4 часа назад
    timestamp_data = {'last_check_time': time.time() - 14400}
    timestamp_file.write_text(json.dumps(timestamp_data), encoding='utf-8')
    
    # Создаем конфиг с интервалом 1 час
    config_data = {'check_interval_seconds': 3600}
    config_file.write_text(json.dumps(config_data), encoding='utf-8')
    
    with patch('src.healthcheck.Path') as mock_path:
        def path_side_effect(path_str):
            if '.last_check_timestamp.json' in path_str:
                return timestamp_file
            elif 'config.json' in path_str:
                return config_file
            return Path(path_str)
        
        mock_path.side_effect = path_side_effect
        result = healthcheck.check_health()
    
    assert result is False


def test_healthcheck_invalid_json(tmp_path):
    """Тест: при невалидном JSON health check проваливается"""
    timestamp_file = tmp_path / '.last_check_timestamp.json'
    timestamp_file.write_text("invalid json", encoding='utf-8')
    
    with patch('src.healthcheck.Path') as mock_path:
        mock_path.return_value = timestamp_file
        result = healthcheck.check_health()
    
    assert result is False


def test_healthcheck_missing_timestamp_in_json(tmp_path):
    """Тест: при отсутствии timestamp в JSON health check проваливается"""
    timestamp_file = tmp_path / '.last_check_timestamp.json'
    timestamp_file.write_text(json.dumps({'some_other_field': 123}), encoding='utf-8')
    
    with patch('src.healthcheck.Path') as mock_path:
        mock_path.return_value = timestamp_file
        result = healthcheck.check_health()
    
    assert result is False


def test_healthcheck_uses_default_interval_if_config_missing(tmp_path):
    """Тест: использует дефолтный интервал если конфиг недоступен (упрощенный)"""
    # Этот тест проверяет, что при отсутствии config.json используется дефолтный интервал
    # Реальная проверка происходит в интеграционном тесте
    # Здесь просто проверяем, что при первом запуске health check возвращает True
    with patch('src.healthcheck.Path') as mock_path:
        mock_instance = mock_path.return_value
        mock_instance.exists.return_value = False
        result = healthcheck.check_health()
    
    assert result is True
