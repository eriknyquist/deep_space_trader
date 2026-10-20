; Inno Setup script for the Windows installer (needs Inno Setup 6.0 or newer).
;
; Build the game with PyInstaller first (pyinstaller deep_space_trader.spec), then
; compile this script. All paths are relative to this file's folder, so it works
; from any checkout of the project. The installer is saved in Output\.
;
; The images and the license copy in installer\ are made by
; scripts\make_installer_files.py (only needed to change them).

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{8E361029-9398-4236-B388-00D4C4D2F1D1}
AppName=Deep Space Trader
AppVersion=1.5.0
;AppVerName=Deep Space Trader 1.5.0
AppPublisher=Erik Nyquist
AppPublisherURL=https://github.com/eriknyquist/deep_space_trader
AppSupportURL=https://github.com/eriknyquist/deep_space_trader/issues
AppUpdatesURL=https://github.com/eriknyquist/deep_space_trader/releases
OutputBaseFilename=deep-space-trader-1.5.0
Compression=lzma
SolidCompression=yes

; A 64-bit game: only installs on 64-bit Windows, and into "Program Files"
; (not "Program Files (x86)"). ("x64" works in every Inno Setup 6 version;
; 6.3 and newer also call it "x64compatible")
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Players can choose to install for all users (needs administrator rights), or
; just for themselves (no administrator rights needed). {autopf} and the other
; {auto...} folders follow that choice
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\Deep Space Trader
DefaultGroupName=Deep Space Trader

; If the game is running when installing or uninstalling, offer to close it
CloseApplications=yes

; Looks
WizardStyle=modern
SetupIconFile=deep_space_trader\images\icon.ico
UninstallDisplayIcon={app}\_internal\images\icon.ico
; (Several sizes, for high-DPI screens: Inno Setup picks the best one)
WizardImageFile=installer\wizard_image_164x314.bmp,installer\wizard_image_246x459.bmp,installer\wizard_image_328x628.bmp
WizardSmallImageFile=installer\wizard_small_image_55x55.bmp,installer\wizard_small_image_83x80.bmp,installer\wizard_small_image_110x106.bmp

; The MIT license, shown before installing
LicenseFile=installer\license.txt

[Languages]
; The installer uses the Windows language if it's one of these (as the game
; does), and English otherwise
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\Deep Space Trader\Deep Space Trader.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Deep Space Trader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\Deep Space Trader"; Filename: "{app}\Deep Space Trader.exe"; IconFilename: "{app}\_internal\images\icon.ico"
Name: "{autodesktop}\Deep Space Trader"; Filename: "{app}\Deep Space Trader.exe"; IconFilename: "{app}\_internal\images\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\Deep Space Trader.exe"; Description: "{cm:LaunchProgram,Deep Space Trader}"; Flags: nowait postinstall skipifsilent
