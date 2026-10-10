; Inno Setup 6.7+ / standard per-user install. Private data is outside {app}.
#ifndef AppVersion
  #define AppVersion "1.9.3"
#endif
#ifndef AppSource
  #define AppSource "..\dist\LISA-App"
#endif
#ifndef OutputPath
  #define OutputPath "..\dist"
#endif

[Setup]
AppId={{A8F7C393-8F62-4CD1-ACE5-65F949F74543}
AppName=LISA Companion
AppVersion={#AppVersion}
AppVerName=LISA {#AppVersion}
AppPublisher=Kitty Corp
AppPublisherURL=https://github.com/psychspy7/lisa-companion
AppSupportURL=https://github.com/psychspy7/lisa-companion/issues
AppUpdatesURL=https://github.com/psychspy7/lisa-companion/releases/latest
DefaultDirName={localappdata}\Programs\LISA
DefaultGroupName=LISA
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#OutputPath}
OutputBaseFilename=LISA-Setup
SetupIconFile=..\assets\lisa.ico
UninstallDisplayIcon={app}\LISA-icon-{#AppVersion}.ico
UninstallDisplayName=LISA Companion
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern dark polar includetitlebar
WizardSizePercent=110
DisableStartupPrompt=yes
DisableProgramGroupPage=yes
CloseApplications=yes
RestartApplications=no
SetupMutex=KittyCorp.LISA.Setup
SetupLogging=yes
CloseApplicationsFilter=*.exe,*.dll,*.pyd
#ifdef TestBuild
CreateUninstallRegKey=no
UsePreviousAppDir=no
UsePreviousTasks=no
#else
UsePreviousTasks=yes
UsePreviousAppDir=yes
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Add a LISA shortcut to my Desktop"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "{#AppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\lisa.ico"; DestDir: "{app}"; DestName: "LISA-icon-{#AppVersion}.ico"; Flags: ignoreversion
Source: "{#AppSource}\_internal\updater\LISA-Updater.exe"; DestName: "LISA-Install-Helper.exe"; Flags: dontcopy

[Icons]
Name: "{code:StartMenuDir}\LISA"; Filename: "{app}\LISA.exe"; WorkingDir: "{app}"; IconFilename: "{app}\LISA-icon-{#AppVersion}.ico"; Comment: "Talk to Lisa"
Name: "{code:DesktopDir}\LISA"; Filename: "{app}\LISA.exe"; WorkingDir: "{app}"; IconFilename: "{app}\LISA-icon-{#AppVersion}.ico"; Comment: "Talk to Lisa"; Tasks: desktopicon

[Run]
Filename: "{app}\LISA.exe"; Description: "Open Lisa now"; Flags: nowait postinstall skipifsilent; Check: CanLaunch

[Messages]
WelcomeLabel1=Welcome to LISA
WelcomeLabel2=Your own space to talk, unwind and spend time with Lisa.%n%nSetup installs Lisa for your Windows account. You can add a Desktop shortcut on the next pages.%n%nYour saved memories, chats and API keys stay in Lisa's private data folder when you update or uninstall.
FinishedHeadingLabel=Lisa is ready, Sir.
FinishedLabel=Lisa has been installed. Your shortcut opens the separate full-screen app.

[Code]
function IsUpdate: Boolean;
var
  I: Integer;
begin
  Result := False;
  for I := 1 to ParamCount do
    if CompareText(ParamStr(I), '/UPDATE') = 0 then
      Result := True;
end;

function CanLaunch: Boolean;
begin
  Result := not IsUpdate;
end;

function DesktopDir(Param: String): String;
begin
#ifdef TestBuild
  Result := ExtractFileDir(ExpandConstant('{app}')) + '\Desktop';
#else
  Result := ExpandConstant('{userdesktop}');
#endif
end;

function StartMenuDir(Param: String): String;
begin
#ifdef TestBuild
  Result := ExtractFileDir(ExpandConstant('{app}')) + '\Start Menu\LISA';
#else
  Result := ExpandConstant('{userprograms}\LISA');
#endif
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Target, PrivateData, ErrorPath: String;
  ExitCode: Integer;
  Details: AnsiString;
begin
  Result := '';
  Target := AddBackslash(ExpandFileName(ExpandConstant('{app}')));
  PrivateData := AddBackslash(ExpandFileName(ExpandConstant('{localappdata}\LISA')));
  if (CompareText(Target, PrivateData) = 0) or
     (CompareText(Copy(Target, 1, Length(PrivateData)), PrivateData) = 0) then
    Result := 'Choose a different installation folder. This folder holds Lisa''s private memories and settings.';
  if Result <> '' then Exit;
  if CompareText(Target, AddBackslash(ExtractFileDrive(Target))) = 0 then begin
    Result := 'Choose a dedicated Lisa installation folder, not the root of a drive.';
    Exit;
  end;
  WizardForm.StatusLabel.Caption := 'Preparing Lisa and checking folder access...';
  ExtractTemporaryFile('LISA-Install-Helper.exe');
  ErrorPath := ExpandConstant('{tmp}\lisa-install-error.txt');
  DeleteFile(ErrorPath);
  if not Exec(ExpandConstant('{tmp}\LISA-Install-Helper.exe'),
      '--prepare-install "' + Target + 'LISA.exe" "' + ErrorPath + '"',
      ExpandConstant('{tmp}'), SW_HIDE, ewWaitUntilTerminated, ExitCode) then begin
    Result := 'Windows could not start the installation check. Retry Setup. Windows error: ' + IntToStr(ExitCode);
    Exit;
  end;
  if ExitCode <> 0 then begin
    if LoadStringFromFile(ErrorPath, Details) then Result := String(Details)
    else Result := 'Lisa could not prepare for installation. Close Lisa and retry Setup.';
  end;
end;

procedure VerifyInstalledFile(RelativeName, ExpectedHash: String);
var Filename: String;
begin
  Filename := ExpandConstant('{app}\') + RelativeName;
  if not FileExists(Filename) then
    RaiseException('A Lisa file was not installed: ' + RelativeName);
  if CompareText(GetSHA256OfFile(Filename), ExpectedHash) <> 0 then
    RaiseException('A Lisa file failed verification: ' + RelativeName + '. Run Setup again to repair it.');
end;

#include VerificationInclude

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    WizardForm.StatusLabel.Caption := 'Verifying Lisa''s installed files...';
    VerifyInstalledPayload;
    Log('LISA installed payload verified: {#AppVersion}');
  end;
end;
