$ErrorActionPreference = "Stop"

# Run only in disposable CI: install into the runner's temp folder, launch the
# installed app against a temporary database, then uninstall it again.
$Installer = Get-ChildItem -LiteralPath ".\release" -Filter "ExpenseTracker-Setup-*-x64.exe" |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $Installer) { throw "No Expense Tracker setup package was created." }

$InstallDirectory = Join-Path $env:RUNNER_TEMP "ExpenseTracker-Installer-Smoke"
$Database = Join-Path $env:RUNNER_TEMP "ExpenseTracker-installer-smoke.sqlite3"
$InstallerLog = Join-Path $env:RUNNER_TEMP "ExpenseTracker-installer-smoke.log"
$Setup = Start-Process -FilePath $Installer.FullName `
    -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR=`"$InstallDirectory`" /LOG=`"$InstallerLog`"" `
    -Wait -PassThru
if ($Setup.ExitCode -ne 0) { throw "The installer failed with exit code $($Setup.ExitCode)." }

$Application = Join-Path $InstallDirectory "ExpenseTracker.exe"
if (-not (Test-Path -LiteralPath $Application)) { throw "The installed application executable is missing." }
$env:QT_QPA_PLATFORM = "offscreen"
$env:EXPENSE_DEBUG = "1"
$Process = $null
try {
    $Process = Start-Process -FilePath $Application -ArgumentList "--db $Database" `
        -WorkingDirectory $InstallDirectory -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 8
    $Process.Refresh()
    if ($Process.HasExited) {
        $Log = Join-Path $env:TEMP "ExpenseTracker-startup.log"
        $Details = if (Test-Path -LiteralPath $Log) { Get-Content -LiteralPath $Log -Raw } else { "No startup diagnostic was written." }
        throw "The installed app exited during startup (exit code $($Process.ExitCode)).`n$Details"
    }
    if (-not (Test-Path -LiteralPath $Database)) { throw "The installed app did not create its test database." }
    Write-Host "Setup installed successfully and the installed application opened its local database."
}
finally {
    if ($Process) {
        $Process.Refresh()
        if (-not $Process.HasExited) { Stop-Process -Id $Process.Id -Force }
    }
    $Uninstaller = Join-Path $InstallDirectory "unins000.exe"
    if (Test-Path -LiteralPath $Uninstaller) {
        $Removal = Start-Process -FilePath $Uninstaller -ArgumentList @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART") -Wait -PassThru
        if ($Removal.ExitCode -ne 0) { throw "The test installation could not be removed (exit code $($Removal.ExitCode))." }
    }
}
