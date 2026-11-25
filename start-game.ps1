# Bubble Pop Game Launcher (PowerShell)
# Right-click this file and "Run with PowerShell" or create a shortcut to:
# powershell.exe -ExecutionPolicy Bypass -File "C:\Users\temuri\bubble-pop-game\start-game.ps1"

$gameDir = "C:\Users\temuri\bubble-pop-game"
$port = 8080
$url = "http://localhost:$port"

Write-Host "Starting Bubble Pop Game..." -ForegroundColor Green
Write-Host "Game directory: $gameDir" -ForegroundColor Cyan

# Check if Python is available
try {
    python --version | Out-Null
} catch {
    Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Change to game directory
Set-Location $gameDir

# Check if port is already in use
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
try {
    $listener.Start()
    $listener.Stop()
    $portFree = $true
} catch {
    $portFree = $false
}

if (-not $portFree) {
    Write-Host "Port $port already in use - assuming server is already running" -ForegroundColor Yellow
} else {
    # Start Bubble Pop custom server in background (supports absolute video folder paths)
        Write-Host "Starting HTTP server on $url... " -ForegroundColor Green
        $serverProcess = Start-Process python -ArgumentList "server.py" -WorkingDirectory $gameDir -WindowStyle Minimized -PassThru
    
    # Wait for server to start
    Start-Sleep -Seconds 2
    
    Write-Host "Server started (PID: $($serverProcess.Id))" -ForegroundColor Cyan
}

# Open in default browser
Write-Host "Opening game in browser..." -ForegroundColor Green
Start-Process $url

Write-Host "`nGame opened! Enjoy!" -ForegroundColor Green
Write-Host "To stop the server, close the minimized Python window or run:" -ForegroundColor Gray
Write-Host "  taskkill /f /im python.exe" -ForegroundColor Gray
Write-Host "`nPress Enter to exit this launcher (server keeps running)..." -ForegroundColor Gray
Read-Host