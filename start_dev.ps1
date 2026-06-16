# ============================================================
#  DialFlow Pro -- Development Launcher
#  Starts: Daphne, Celery Worker, Celery Beat, Vite frontend
#  Each service gets its own window; logs go to logs\*.log
# ============================================================

$Root     = $PSScriptRoot
$Backend  = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Logs     = Join-Path $Root "logs"

# Create logs dir and clear old files
New-Item -ItemType Directory -Force -Path $Logs | Out-Null
foreach ($name in @("django","celery_worker","celery_beat","frontend")) {
    [IO.File]::WriteAllText("$Logs\$name.log", "")
}

# ── Helper: launch a service in its own PowerShell window ────────────────────
#  The script block is base64-encoded so there are zero quoting issues.
function Start-Service {
    param([string]$Title, [string]$Script)

    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Script))
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-EncodedCommand", $encoded
    )
    Start-Sleep -Milliseconds 400   # slight gap so windows open in order
    Write-Host "  started  $Title" -ForegroundColor Green
}

# ── 1. Daphne (Django ASGI) ───────────────────────────────────────────────────
Start-Service "Daphne (8000)" @"
`$Host.UI.RawUI.WindowTitle = 'Daphne (8000)  -  DialFlow'
`$Host.UI.RawUI.ForegroundColor = 'Green'
Clear-Host
Write-Host ''
Write-Host '  +--------------------------------------------+' -ForegroundColor Green
Write-Host '  |  Daphne ASGI  --  http://0.0.0.0:8000     |' -ForegroundColor Green
Write-Host '  |  Log: $Logs\django.log                     |' -ForegroundColor DarkGreen
Write-Host '  +--------------------------------------------+' -ForegroundColor Green
Write-Host ''
Set-Location '$Backend'
. '$Backend\venv\Scripts\Activate.ps1'
`$env:PYTHONUNBUFFERED            = '1'
`$env:DJANGO_SETTINGS_MODULE      = 'config.settings.development'
cmd /c "daphne -b 0.0.0.0 -p 8000 config.asgi:application 2>&1" |
    Tee-Object -FilePath '$Logs\django.log' -Append
"@

# ── 2. Celery Worker ──────────────────────────────────────────────────────────
Start-Service "Celery Worker" @"
`$Host.UI.RawUI.WindowTitle = 'Celery Worker  -  DialFlow'
`$Host.UI.RawUI.ForegroundColor = 'Cyan'
Clear-Host
Write-Host ''
Write-Host '  +--------------------------------------------+' -ForegroundColor Cyan
Write-Host '  |  Celery Worker  --  pool: solo (Windows)   |' -ForegroundColor Cyan
Write-Host '  |  Queues: default, campaigns, calls         |' -ForegroundColor Cyan
Write-Host '  |  Log: $Logs\celery_worker.log              |' -ForegroundColor DarkCyan
Write-Host '  +--------------------------------------------+' -ForegroundColor Cyan
Write-Host ''
Set-Location '$Backend'
. '$Backend\venv\Scripts\Activate.ps1'
`$env:PYTHONUNBUFFERED            = '1'
`$env:DJANGO_SETTINGS_MODULE      = 'config.settings.development'
cmd /c "celery -A config worker -l info -P solo -Q default,campaigns,calls,celery 2>&1" |
    Tee-Object -FilePath '$Logs\celery_worker.log' -Append
"@

# ── 3. Celery Beat ────────────────────────────────────────────────────────────
Start-Service "Celery Beat" @"
`$Host.UI.RawUI.WindowTitle = 'Celery Beat  -  DialFlow'
`$Host.UI.RawUI.ForegroundColor = 'Yellow'
Clear-Host
Write-Host ''
Write-Host '  +--------------------------------------------+' -ForegroundColor Yellow
Write-Host '  |  Celery Beat  --  campaign heartbeat: 60s  |' -ForegroundColor Yellow
Write-Host '  |  Log: $Logs\celery_beat.log                |' -ForegroundColor DarkYellow
Write-Host '  +--------------------------------------------+' -ForegroundColor Yellow
Write-Host ''
Set-Location '$Backend'
. '$Backend\venv\Scripts\Activate.ps1'
`$env:PYTHONUNBUFFERED            = '1'
`$env:DJANGO_SETTINGS_MODULE      = 'config.settings.development'
cmd /c "celery -A config beat -l info 2>&1" |
    Tee-Object -FilePath '$Logs\celery_beat.log' -Append
"@

# ── 4. Vite frontend ──────────────────────────────────────────────────────────
Start-Service "Frontend (5173)" @"
`$Host.UI.RawUI.WindowTitle = 'Frontend (5173)  -  DialFlow'
`$Host.UI.RawUI.ForegroundColor = 'Magenta'
Clear-Host
Write-Host ''
Write-Host '  +--------------------------------------------+' -ForegroundColor Magenta
Write-Host '  |  Vite  --  http://localhost:5173            |' -ForegroundColor Magenta
Write-Host '  |  Log: $Logs\frontend.log                   |' -ForegroundColor DarkMagenta
Write-Host '  +--------------------------------------------+' -ForegroundColor Magenta
Write-Host ''
Set-Location '$Frontend'
cmd /c "npm run dev 2>&1" |
    Tee-Object -FilePath '$Logs\frontend.log' -Append
"@

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ''
Write-Host '  +================================================+' -ForegroundColor White
Write-Host '  |   DialFlow Pro  --  All services launched!     |' -ForegroundColor White
Write-Host '  |                                                 |' -ForegroundColor White
Write-Host '  |   Frontend  :  http://localhost:5173            |' -ForegroundColor White
Write-Host '  |   Backend   :  http://localhost:8000            |' -ForegroundColor White
Write-Host '  |   API       :  http://localhost:8000/api/       |' -ForegroundColor White
Write-Host '  |                                                 |' -ForegroundColor White
Write-Host "  |   Logs      :  $Logs" -ForegroundColor White
Write-Host '  |                                                 |' -ForegroundColor White
Write-Host '  |   Tail log  :  Get-Content logs\django.log -Wait  |' -ForegroundColor DarkGray
Write-Host '  |   Stop all  :  close each colored window        |' -ForegroundColor DarkGray
Write-Host '  |                                                 |' -ForegroundColor DarkGray
Write-Host '  |   WSL needs port 8000 open in Windows Firewall  |' -ForegroundColor DarkYellow
Write-Host '  |   Run as Admin if not yet done:                 |' -ForegroundColor DarkYellow
Write-Host '  |   New-NetFirewallRule -DisplayName "DialFlow"   |' -ForegroundColor DarkYellow
Write-Host '  |     -Direction Inbound -Protocol TCP            |' -ForegroundColor DarkYellow
Write-Host '  |     -LocalPort 8000 -Action Allow               |' -ForegroundColor DarkYellow
Write-Host '  +================================================+' -ForegroundColor White
Write-Host ''
