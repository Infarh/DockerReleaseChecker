@echo off
setlocal

set "IMAGE_NAME=infarh/docker-release-checker"
set "IMAGE_TAG=latest"
set "CONTAINER_NAME=docker-release-checker"
set "DOWNLOAD_DIR=D:\!Downloads\Docker"
set "CONFIG_FILE=D:\!Downloads\Docker\config.json"

if not exist "%DOWNLOAD_DIR%" (
    echo [ERROR] Directory does not exist: %DOWNLOAD_DIR%
    exit /b 1
)

if not exist "%CONFIG_FILE%" (
    echo [ERROR] Config file does not exist: %CONFIG_FILE%
    exit /b 1
)

echo [INFO] Stopping old container (if exists)...
docker rm -f %CONTAINER_NAME% >nul 2>&1

echo [INFO] Starting container %CONTAINER_NAME%...
docker run -d ^
  --name %CONTAINER_NAME% ^
  --restart unless-stopped ^
    --health-cmd "python -m src.healthcheck" ^
    --health-interval 2m ^
    --health-timeout 10s ^
    --health-start-period 30s ^
    --health-retries 3 ^
  -v "%DOWNLOAD_DIR%:/downloads" ^
  -v "%CONFIG_FILE%:/app/config.json:ro" ^
  %IMAGE_NAME%:%IMAGE_TAG%

if errorlevel 1 (
    echo [ERROR] Container start failed
    exit /b 1
)

echo [INFO] Container started successfully
echo [INFO] Logs: docker logs -f %CONTAINER_NAME%
