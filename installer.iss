; Inno Setup — empaqueta dist/traslatetool en un instalador de un solo clic.
; Se compila en Windows:  iscc installer.iss
; El runner windows-latest de GitHub Actions ya trae Inno Setup instalado.

#define AppName "traslatetool"
#define AppVersion "0.1.0"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=dist
OutputBaseFilename=traslatetool-setup
Compression=lzma2
SolidCompression=yes
; Instala por usuario: sin UAC, y la app necesita correr en la sesión del
; usuario para poder leer la selección y enviar Ctrl+V.
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern

[Files]
Source: "dist\traslatetool\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\traslatetool.exe"
Name: "{group}\{#AppName} (diagnostico)"; Filename: "{app}\traslatetool-debug.exe"
Name: "{userstartup}\{#AppName}"; Filename: "{app}\traslatetool.exe"

[Run]
Filename: "{app}\traslatetool.exe"; Description: "Iniciar traslatetool"; Flags: nowait postinstall skipifsilent
