#define AppName "Expense Tracker"
#ifndef AppVersion
#define AppVersion "2.0.0"
#endif
#define AppPublisher "Homafar Sharifi"
#define AppExeName "ExpenseTracker.exe"

[Setup]
AppId={{F1E03671-4242-4CF4-86D3-036888C808A1}
AppName={#AppName}
AppPublisher={#AppPublisher}
AppVersion={#AppVersion}
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} Windows installer
VersionInfoProductName={#AppName}
DefaultDirName={localappdata}\Programs\Expense Tracker
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=ExpenseTracker-Setup-{#AppVersion}-x64
SetupIconFile=..\assets\expense-tracker.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\ExpenseTracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: postinstall nowait skipifsilent

; User data remains under %LOCALAPPDATA%\ExpenseTracker after uninstall.
