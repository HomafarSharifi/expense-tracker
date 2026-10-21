$ErrorActionPreference = "Stop"

# Exercise the frozen app before creating a setup package. Offscreen mode lets
# CI initialize Qt without a user session; a created database proves the UI
# reached its normal startup path, and a still-running process proves it opened.
$env:QT_QPA_PLATFORM = "offscreen"
$env:EXPENSE_DEBUG = "1"
$SmokeDirectory = ".test-tmp"
$SmokeName = "bundle-smoke-{0}.sqlite3" -f [guid]::NewGuid().ToString("N")
$SmokeDatabase = Join-Path $SmokeDirectory $SmokeName
New-Item -ItemType Directory -Force -Path $SmokeDirectory | Out-Null
$Process = Start-Process -FilePath ".\dist\ExpenseTracker\ExpenseTracker.exe" `
    -ArgumentList "--db $SmokeDatabase" -WorkingDirectory (Get-Location).Path -PassThru -WindowStyle Hidden
try {
    Start-Sleep -Seconds 8
    $Process.Refresh()
    if ($Process.HasExited) {
        $Log = Join-Path $env:TEMP "ExpenseTracker-startup.log"
        $Details = if (Test-Path -LiteralPath $Log) { Get-Content -LiteralPath $Log -Raw } else { "No startup diagnostic was written." }
        throw "The packaged app exited during startup (exit code $($Process.ExitCode)).`n$Details"
    }
    if (-not (Test-Path -LiteralPath $SmokeDatabase)) {
        throw "The packaged app did not create its test database."
    }
    Write-Host "Packaged Windows app started and opened a fresh SQLite database."
}
finally {
    $Process.Refresh()
    if (-not $Process.HasExited) { Stop-Process -Id $Process.Id -Force }
    foreach ($Path in @($SmokeDatabase, "$SmokeDatabase-wal", "$SmokeDatabase-shm")) {
        Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    }
}
