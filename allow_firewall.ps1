# DropCast & AirCasta - Windows Firewall Setup
# Encoding: UTF-8 with BOM

try {
    [Console]::InputEncoding  = [System.Text.Encoding]::UTF8
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding           = [System.Text.Encoding]::UTF8
} catch {}

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

Clear-Host
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "    DropCast & AirCasta - Windows Firewall Setup       " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

try {
    # 1. Clean existing rules
    Remove-NetFirewallRule -DisplayName "DropCast (AirCasta)" -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -DisplayName "AirCasta AirPlay TCP" -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -DisplayName "AirCasta AirPlay UDP" -ErrorAction SilentlyContinue

    # 2. Add DropCast TCP 7080
    Write-Host "[1/3] Настройка порта DropCast (TCP 7080)..." -ForegroundColor Yellow
    New-NetFirewallRule -DisplayName "DropCast (AirCasta)" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 7080 -Profile Any | Out-Null
    Write-Host "  -> Порт 7080 открыт для всех сетей [OK]" -ForegroundColor Green

    # 3. Add AirPlay ports
    Write-Host "[2/3] Настройка портов AirPlay (TCP 7000-7100, UDP 6000-7011)..." -ForegroundColor Yellow
    New-NetFirewallRule -DisplayName "AirCasta AirPlay TCP" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 7000, 7001, 7100 -Profile Any | Out-Null
    New-NetFirewallRule -DisplayName "AirCasta AirPlay UDP" -Direction Inbound -Action Allow -Protocol UDP -LocalPort 6000, 6001, 7011 -Profile Any | Out-Null
    Write-Host "  -> Порты AirPlay открыты [OK]" -ForegroundColor Green

    # 4. Update python.exe rules to Any profile
    Write-Host "[3/3] Настройка доступа Python в домашней сети..." -ForegroundColor Yellow
    Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*python*" } | Set-NetFirewallRule -Profile Any -ErrorAction SilentlyContinue
    Write-Host "  -> Доступ Python расширен (Private/Public) [OK]" -ForegroundColor Green

    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "  [УСПЕШНО / SUCCESS] Доступ для iPhone полностью открыт!" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Веб-интерфейс DropCast: http://192.168.1.201:7080" -ForegroundColor White
}
catch {
    Write-Host "[ОШИБКА] Не удалось применить правила: $_" -ForegroundColor Red
}

Write-Host ""
Read-Host "Нажмите Enter для выхода..."
