[Setup]
AppId={{3C55BED1-5D79-4B40-9C53-5A27106773B8}
AppName=JARVIS Foundation
AppVersion=0.4.0
DefaultDirName={localappdata}\Programs\JARVIS-Foundation
DefaultGroupName=JARVIS Foundation
PrivilegesRequired=lowest
OutputDir=..\installer-output
OutputBaseFilename=JARVIS-Foundation-Phase0-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\JARVIS-Foundation.exe
[Files]
Source: "..\dist\JARVIS-Foundation\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY.md"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\JARVIS Foundation"; Filename: "{app}\JARVIS-Foundation.exe"
Name: "{autodesktop}\JARVIS Foundation"; Filename: "{app}\JARVIS-Foundation.exe"
[Run]
Filename: "{app}\JARVIS-Foundation.exe"; Description: "Open JARVIS Foundation"; Flags: nowait postinstall skipifsilent
