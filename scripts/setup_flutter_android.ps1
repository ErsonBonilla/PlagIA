# ============================================================================
# PLAGIA ENTERPRISE - CONFIGURACION FLUTTER + ANDROID STUDIO (WINDOWS)
# ============================================================================
$ErrorActionPreference = "Continue"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " PlagIA Enterprise - Verificacion de Flutter 3.47+ y Android Studio SDK" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

# Recargar PATH del registro de Windows en la sesion actual
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

# Configurar ANDROID_HOME si existe en la ruta por defecto de Android Studio
$defaultAndroidSdk = "$env:LOCALAPPDATA\Android\Sdk"
if (Test-Path $defaultAndroidSdk) {
    $env:ANDROID_HOME = $defaultAndroidSdk
    $env:ANDROID_SDK_ROOT = $defaultAndroidSdk
    Write-Host "[OK] ANDROID_HOME configurado en: $defaultAndroidSdk" -ForegroundColor Green
}

Write-Host "`n[1/3] Verificando versiones de Flutter y Dart..." -ForegroundColor Yellow
flutter --version
dart --version

Write-Host "`n[2/3] Inicializando dependencias en mobile_app/..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\..\mobile_app"
flutter pub get
Write-Host "`n[3/3] Ejecutando analisis estatico de codigo Dart (dart analyze)..." -ForegroundColor Yellow
dart analyze
Pop-Location

Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host " Proyecto Flutter listo para abrir en Android Studio:" -ForegroundColor Green
Write-Host "   Ruta: C:\Users\erson\Documents\Programación\ISIDEAD\PlagIA\mobile_app" -ForegroundColor White
Write-Host "============================================================================" -ForegroundColor Cyan
