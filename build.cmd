@echo off
setlocal

set "IMAGE_NAME=ghcr.io/infarh/docker-release-checker"
set "IMAGE_TAG=latest"

echo [INFO] Building image %IMAGE_NAME%:%IMAGE_TAG%...
docker build -t %IMAGE_NAME%:%IMAGE_TAG% .
if errorlevel 1 (
    echo [ERROR] Build failed
    exit /b 1
)

echo [INFO] Build completed successfully
