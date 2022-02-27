; Script generated by the Inno Script Studio Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{8E361029-9398-4236-B388-00D4C4D2F1D1}
AppName=Deep Space Trader
AppVersion=1.2.3
;AppVerName=Deep Space Trader 1.2.3
AppPublisher=Erik Nyquist
AppPublisherURL=http://www.ekn.io
AppSupportURL=http://www.ekn.io
AppUpdatesURL=http://www.ekn.io
DefaultDirName={pf}\Deep Space Trader
DefaultGroupName=Deep Space Trader
OutputBaseFilename=deep-space-trader-1.2.3
SetupIconFile=C:\Users\Gamer\deep_space_trader\deep_space_trader\images\icon.ico
Compression=lzma
SolidCompression=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Users\Gamer\deep_space_trader\dist\Deep Space Trader\Deep Space Trader.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Gamer\deep_space_trader\dist\Deep Space Trader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\Deep Space Trader"; Filename: "{app}\Deep Space Trader.exe"; IconFilename: {app}\images\icon.ico
Name: "{commondesktop}\Deep Space Trader"; Filename: "{app}\Deep Space Trader.exe"; IconFilename: {app}\images\icon.ico; Tasks: desktopicon

[Run]
Filename: "{app}\Deep Space Trader.exe"; Description: "{cm:LaunchProgram,Deep Space Trader}"; Flags: nowait postinstall skipifsilent