<# : batch
@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "iex (Get-Content -Raw -LiteralPath '%~f0')"
pause
exit /b
#>
$ErrorActionPreference = 'Stop'
$here = (Get-Location).Path
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Write-Host ''
Write-Host '=== TELEGRAM BOT SETUP ===' -ForegroundColor Yellow
Write-Host ''
$token = (Read-Host 'Paste bot TOKEN from @BotFather and press Enter').Trim()
if (-not $token) { Write-Host 'No token. Exit.' -ForegroundColor Red; exit }

try {
    $me = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getMe"
} catch {
    Write-Host 'Token is wrong or no internet. Check and run again.' -ForegroundColor Red
    exit
}
$botName = $me.result.username
Write-Host ''
Write-Host "Bot found: @$botName" -ForegroundColor Green
Write-Host ''
Write-Host "Now open Telegram, find @$botName, press START (or write any message)." -ForegroundColor Cyan
Read-Host 'Then come back here and press Enter'

$chatId = $null
for ($i = 0; $i -lt 10 -and -not $chatId; $i++) {
    $upd = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getUpdates"
    $msg = $upd.result | Where-Object { $_.message } | Select-Object -Last 1
    if ($msg) { $chatId = $msg.message.chat.id } else { Start-Sleep -Seconds 2 }
}
if (-not $chatId) {
    Write-Host "No message found. Write something to @$botName and run this file again." -ForegroundColor Red
    exit
}

$envText = "TELEGRAM_BOT_TOKEN=$token`r`nTELEGRAM_CHAT_ID=$chatId`r`nMETA_PIXEL_ID=`r`n"
[IO.File]::WriteAllText((Join-Path $here '.env'), $envText)

$body = @{ chat_id = $chatId; text = 'OK! Zayavki s saita budut prihodit syuda.' }
Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/sendMessage" -Method Post -Body $body | Out-Null

Write-Host ''
Write-Host 'DONE! Check Telegram - the bot sent you a message.' -ForegroundColor Green
Write-Host 'Now CLOSE the black zapusk window and run zapusk again.' -ForegroundColor Yellow
