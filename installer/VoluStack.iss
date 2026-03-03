#define MyAppName "VoluStack"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "OOMrConrλdo"
#define MyAppURL "https://github.com/OOMrConrado/VoluStack"
#define MyAppExeName "volustack.exe"
#define MyAppDescription "Per-application volume control for Windows"
#define MyAppCopyright "Copyright (c) 2026 OOMrConrλdo"
[Setup]
AppId={{7A3B8E2F-1D4C-4E9A-B5F2-8C6D9E1F3A2B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
AppCopyright={#MyAppCopyright}
AppContact={#MyAppURL}/issues
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppDescription}
VersionInfoCopyright={#MyAppCopyright}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=VoluStack-Setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2/max
SolidCompression=yes
MinVersion=10.0.17763
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern
WizardSizePercent=120,120
DisableWelcomePage=no
ShowLanguageDialog=yes
CloseApplications=force
RestartApplications=no
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
[Messages]
english.WelcomeLabel1=Welcome to [name] Setup
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nVoluStack gives you per-application volume control right from your desktop.%n%nIt is recommended that you close all other applications before continuing.
english.FinishedHeadingLabel=Installation Complete
english.FinishedLabel=[name] has been successfully installed on your computer.%n%nEnjoy full control over your audio
spanish.WelcomeLabel1=Bienvenido al instalador de [name]
spanish.WelcomeLabel2=Se instalará [name/ver] en su equipo.%n%nVoluStack le permite controlar el volumen de cada aplicación directamente desde su escritorio.%n%nSe recomienda cerrar todas las demás aplicaciones antes de continuar.
spanish.FinishedHeadingLabel=Instalación completada
spanish.FinishedLabel=[name] se ha instalado correctamente en su equipo.%n%nDisfruta del control total de tu audio
[CustomMessages]
english.AdditionalOptions=Additional options:
english.StartWithWindows=Start VoluStack when Windows starts
spanish.AdditionalOptions=Opciones adicionales:
spanish.StartWithWindows=Iniciar VoluStack con Windows
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalOptions}"; Flags: unchecked
Name: "startupentry"; Description: "{cm:StartWithWindows}"; GroupDescription: "{cm:AdditionalOptions}"
[Files]
Source: "..\dist\VoluStack\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "{#MyAppDescription}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
[Registry]
Root: HKCU; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; ValueName: "VoluStack"; ValueData: """{app}\{#MyAppExeName}"" --minimized"; ValueType: string; Flags: uninsdeletevalue; Tasks: startupentry
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#MyAppExeName}"; Parameters: "--minimized"; Flags: nowait skipifnotsilent
[UninstallDelete]
Type: filesandordirs; Name: "{app}"
[UninstallRun]
Filename: "taskkill"; Parameters: "/F /IM {#MyAppExeName}"; Flags: runhidden; RunOnceId: "KillApp"
[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
ResultCode: Integer;
begin
Exec('taskkill', '/F /IM {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
Result := '';
end;
function InitializeSetup(): Boolean;
begin
Result := True;
if WizardSilent then
begin
Log('Running in silent update mode');
end;
end;
