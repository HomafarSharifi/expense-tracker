$ErrorActionPreference = "Stop"

# Build on Windows: PyInstaller bundles Python and the desktop dependencies.
if (-not (Test-Path ".build-venv\Scripts\python.exe")) {
    py -3.11 -m venv .build-venv
}
$Python = (Resolve-Path ".build-venv\Scripts\python.exe").Path
$PythonVersion = & $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($PythonVersion -ne "3.11") {
    throw "The Windows release bundle must use Python 3.11; .build-venv currently uses $PythonVersion. Recreate .build-venv with 'py -3.11 -m venv .build-venv' and run this script again."
}
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not update pip in .build-venv." }
& $Python -m pip install -e ".[build]"
if ($LASTEXITCODE -ne 0) { throw "Could not install the Windows desktop build dependencies." }
& $Python -m PyInstaller --noconfirm --clean --windowed --onedir `
    --name ExpenseTracker `
    --icon assets\expense-tracker.ico `
    --hidden-import matplotlib.backends.backend_qtagg `
    --exclude-module streamlit --exclude-module pandas --exclude-module pyarrow --exclude-module mysql.connector `
    --add-data "assets;assets" `
    app.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE." }
& .\tools\smoke_windows_bundle.ps1
Write-Host "Build ready in dist\ExpenseTracker. Open installer\ExpenseTracker.iss with Inno Setup to create Setup.exe."


