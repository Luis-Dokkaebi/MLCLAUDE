; ==========================================================
; Inno Setup Script - Oficina Eficiencia
; Genera un instalador profesional a partir de dist\gui_app\
; ==========================================================

#define MyAppName "Oficina Eficiencia"
#define MyAppVersion "1.3.0"
#define MyAppPublisher "Tu Empresa"
#define MyAppExeName "OficinaEficiencia_VMS.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-AB12-CD34EF567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\OficinaEficiencia
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=setup_oficina_eficiencia_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
SetupIconFile=
WizardStyle=modern

; Don't require admin for per-user install
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"

[Files]
; Copy the entire PyInstaller output directory
Source: "dist\OficinaEficiencia_VMS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent
