$ErrorActionPreference = "Stop"

# Keep Python's temporary wheels inside the writable project folder. On some
# managed Windows setups the system TEMP directory blocks ensurepip writes.
$BuildTemp = Join-Path (Get-Location).Path ".tmp-pip"
New-Item -ItemType Directory -Force -Path $BuildTemp | Out-Null
$env:TEMP = $BuildTemp
$env:TMP = $BuildTemp

# Build the Windows release with the project-selected Python runtime. Keeping
# the interpreter check here prevents accidentally shipping another Python.
if (-not (Test-Path ".build-venv\Scripts\python.exe")) {
    $PythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    $CommandVersion = if ($PythonCommand) { & $PythonCommand.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" }
    if ($CommandVersion -eq "3.14") {
        & $PythonCommand.Source -m venv .build-venv
    } else {
        py -3.14 -m venv .build-venv
    }
    if ($LASTEXITCODE -ne 0) { throw "Could not create the Python 3.14 build environment." }
}
$Python = (Resolve-Path ".build-venv\Scripts\python.exe").Path
$PythonVersion = & $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($PythonVersion -ne "3.14") {
    throw "The Windows release bundle must use Python 3.14; .build-venv currently uses $PythonVersion. Move the existing .build-venv aside, then run this script again to create a Python 3.14 environment."
}
if (-not (Test-Path ".build-venv\Scripts\pip.exe")) {
    & $Python -m ensurepip --upgrade --default-pip
    if ($LASTEXITCODE -ne 0) { throw "Could not bootstrap pip in .build-venv." }
}
& $Python -m pip install -e ".[build]"
if ($LASTEXITCODE -ne 0) { throw "Could not install the Windows desktop build dependencies." }
$OriginalPath = $env:PATH
try {
    # PyInstaller scans PATH while resolving imports. Restrict it to Windows and
    # the selected Python so unrelated tools cannot inject incompatible ICU,
    # OpenSSL, or CRT DLLs into the user's app.
    $PythonBase = (& $Python -c "import sys; print(sys.base_prefix)").Trim()
    $env:PATH = @(
        (Join-Path $env:SystemRoot "System32"),
        $env:SystemRoot,
        (Join-Path $env:SystemRoot "System32\Wbem"),
        (Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0"),
        $PythonBase,
        (Join-Path $PythonBase "DLLs"),
        (Split-Path -Parent $Python)
    ) -join ';'
& $Python -m PyInstaller --noconfirm --clean ExpenseTracker.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE." }
}
finally {
    $env:PATH = $OriginalPath
}
& .\tools\smoke_windows_bundle.ps1
Write-Host "Build ready in dist\ExpenseTracker. Open installer\ExpenseTracker.iss with Inno Setup to create Setup.exe."


