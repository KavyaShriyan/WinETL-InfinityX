@echo off
echo ========================================
echo Databricks OAuth Auto-Closer
echo ========================================
echo.
echo Starting background window monitor...
echo This will automatically close OAuth callback windows
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0close_oauth_windows.ps1"
