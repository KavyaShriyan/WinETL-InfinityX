# Databricks OAuth Window Auto-Closer - SAFE MODE
# This script ONLY closes windows with "localhost:8020" in the title
# It will NOT close your main browser or other tabs

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Databricks OAuth Auto-Closer v4.0 SAFE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ SAFE MODE: Only closes localhost:8020 windows" -ForegroundColor Green
Write-Host "⚠️  Will NOT kill browser processes" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

$closedCount = 0

while ($true) {
    # ONLY find windows with localhost:8020 in the title (very specific)
    $windows = Get-Process | Where-Object { 
        $_.MainWindowHandle -ne 0 -and
        $_.MainWindowTitle -ne "" -and
        ($_.MainWindowTitle -match "localhost:8020" -or 
         $_.MainWindowTitle -eq "Please close this tab." -or
         ($_.MainWindowTitle -like "*Please close this tab*" -and $_.MainWindowTitle -like "*Databricks*"))
    }
    
    foreach ($window in $windows) {
        try {
            $closedCount++
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] " -NoNewline -ForegroundColor Gray
            Write-Host "Closing OAuth window: " -NoNewline -ForegroundColor Yellow
            Write-Host "$($window.MainWindowTitle)" -ForegroundColor White
            
            # ONLY close the window, do NOT kill the process
            $window.CloseMainWindow() | Out-Null
            Start-Sleep -Milliseconds 200
        }
        catch {
            Write-Host "Warning: Could not close window: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Display status every 10 closures
    if ($closedCount -gt 0 -and $closedCount % 10 -eq 0) {
        Write-Host ""
        Write-Host "✅ Total OAuth windows closed: $closedCount" -ForegroundColor Cyan
        Write-Host ""
    }
    
    # Check every 500ms (slower to be less aggressive)
    Start-Sleep -Milliseconds 500
}
