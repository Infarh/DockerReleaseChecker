@echo off
setlocal

set "IMAGE_NAME=infarh/docker-release-checker"
set "IMAGE_TAG=latest"

echo [INFO] Building image %IMAGE_NAME%:%IMAGE_TAG%...
docker build -t %IMAGE_NAME%:%IMAGE_TAG% .
if errorlevel 1 (
    echo [ERROR] Build failed
    exit /b 1
)

echo [INFO] Build completed successfully

docker tag %IMAGE_NAME%:%IMAGE_TAG% ghcr.io/%IMAGE_NAME%:%IMAGE_TAG%

docker push ghcr.io/%IMAGE_NAME%:%IMAGE_TAG%
docker push %IMAGE_NAME%:%IMAGE_TAG%