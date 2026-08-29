# Safe, targeted artifact cleaner for AURIX Engine
$ErrorActionPreference = "Continue"

Write-Host "🧹 Cleaning transient Python bytecode, test caches, and build artifacts..." -ForegroundColor Yellow

# Purge Python __pycache__ directories
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Removing: $($_.FullName)" -ForegroundColor DarkGray
    Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
}

# Purge Pytest cache
if (Test-Path ".pytest_cache") {
    Write-Host "  Removing: .pytest_cache" -ForegroundColor DarkGray
    Remove-Item -Path ".pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue
}

# Purge transient Next.js build cache (preserving node_modules)
if (Test-Path "aurix_client\.next\cache") {
    Write-Host "  Removing: aurix_client\.next\cache" -ForegroundColor DarkGray
    Remove-Item -Path "aurix_client\.next\cache" -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "✨ Cache and temporary artifact cleanup completed safely." -ForegroundColor Green
