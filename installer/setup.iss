#define MyAppName "dannyboi's Karaoke"
#define MyAppVersion "3.8"
#define MyAppExeName "DannyboisKaraoke.exe"
[Setup]
AppId={{D1C8C27E-5AB4-48E2-AEA5-1A12F7D52B36}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=dannyboi
DefaultDirName={autopf64}\Dannybois Karaoke
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=Dannybois_Karaoke_v3.8_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\dannyboi.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
[Files]
Source: "..\dist\DannyboisKaraoke\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\dannyboi's Karaoke"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\dannyboi's Karaoke"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch dannyboi's Karaoke"; Flags: nowait postinstall skipifsilent
