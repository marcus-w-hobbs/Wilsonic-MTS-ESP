; Inno Setup script for the 64-bit Wilsonic Windows installer.
;
; Compile from the repo root, after building both projects in Release for x64:
;
;   ISCC.exe /DVersion=0.45.0-beta release\windows\wilsonic.iss
;
; or run release/windows/build-installer.sh, which checks the products first
; and passes the same defines. Every path below is relative to the repo root
; (SourceDir) unless a define overrides it.
;
; Defines:
;   Version          required. The full version string, as in VERSION.txt.
;   WilsonicBuild    x64 Release folder of the Wilsonic VS2022 exporter.
;   ControllerBuild  x64 Release folder of the WilsonicController exporter.
;   MtsEspDir        folder holding Win\64bit\LIBMTS.dll and MTS-ESP.conf.
;   OutputDir        where the installer is written.
;   Signed           define it to sign with the sign tool named wilsonicsign
;                    (ISCC /Swilsonicsign=...) and drop the -unsigned suffix.
;
; The AppId, the install folders and the file list are the ones the v0.43
; installer used (windows_installer_64.iss in the old installer repo), so
; this installer upgrades a v0.43 install in place and Windows shows one
; entry under Apps. Do not change the AppId.

#ifndef Version
  #error Pass the version on the command line: ISCC /DVersion=0.45.0-beta release\windows\wilsonic.iss
#endif
#ifndef WilsonicBuild
  #define WilsonicBuild "Builds\VisualStudio2022\x64\Release"
#endif
#ifndef ControllerBuild
  #define ControllerBuild "Builds\VisualStudio2022-WilsonicController\x64\Release"
#endif
#ifndef MtsEspDir
  #define MtsEspDir "release\mts-esp"
#endif
#ifndef OutputDir
  #define OutputDir "release\out"
#endif

; "0.45.0" from "0.45.0-beta": the file version resource wants numbers only.
#define VersionCore Copy(Version, 1, Pos("-", Version + "-") - 1)

#ifdef Signed
  #define InstallerName "Wilsonic_Win64_v" + Version
#else
  #define InstallerName "Wilsonic_Win64_v" + Version + "-unsigned"
#endif

#define MyAppPublisher "Perfect Buzz Music"
#define MyAppURL "https://wilsonic.co"
#define MyAppName "Wilsonic"
#define MyAppExeName "Wilsonic.exe"
#define MyAppControllerName "WilsonicController"
#define MyAppControllerExeName "WilsonicController.exe"

[Setup]
AppId={{78427BB9-1C86-41AB-BC1F-53E7203BDCDD}
AppName={#MyAppName}
AppVersion={#Version}
AppVerName={#MyAppName} {#Version}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
VersionInfoVersion={#VersionCore}
VersionInfoTextVersion={#Version}
DefaultDirName={autopf}\{#MyAppPublisher}\{#MyAppName}
DisableProgramGroupPage=yes
; v0.43 recorded LIBMTS.dll and MTS-ESP.conf in its uninstall log. Inno Setup
; appends to an existing log by default, so after an upgrade the uninstaller
; would still delete both, whatever the flags below say. Start a fresh log.
; Nothing is orphaned, because this file list is the v0.43 file list.
UninstallLogMode=overwrite
SourceDir=..\..
OutputDir={#OutputDir}
OutputBaseFilename={#InstallerName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; 64-bit only. x64compatible also admits Windows 11 on ARM, which runs x64
; hosts and their x64 plugins under emulation.
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
#ifdef Signed
SignTool=wilsonicsign
SignedUninstaller=yes
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; signonce does nothing unless SignTool is set above.
Source: "{#WilsonicBuild}\Standalone Plugin\Wilsonic.exe"; DestDir: "{app}\{#MyAppName}"; Flags: ignoreversion signonce
Source: "{#ControllerBuild}\Standalone Plugin\WilsonicController.exe"; DestDir: "{app}\{#MyAppControllerName}"; Flags: ignoreversion signonce
; The Projucer builds each VST3 as a bundle folder. v0.43 installed only the
; module inside it, as a single file in a publisher folder, and this keeps
; that layout so an upgrade replaces the old file where it is.
Source: "{#WilsonicBuild}\VST3\Wilsonic.vst3\Contents\x86_64-win\Wilsonic.vst3"; DestDir: "{commoncf}\VST3\{#MyAppPublisher}\{#MyAppName}"; Flags: ignoreversion signonce
Source: "{#ControllerBuild}\VST3\WilsonicController.vst3\Contents\x86_64-win\WilsonicController.vst3"; DestDir: "{commoncf}\VST3\{#MyAppPublisher}\{#MyAppControllerName}"; Flags: ignoreversion signonce
; ODDSound's libMTS, shared by every MTS-ESP plugin on the machine. It is
; overwritten with the pinned build, the config file is written only when
; there is none, and an uninstall of Wilsonic leaves both for the others.
Source: "{#MtsEspDir}\Win\64bit\LIBMTS.dll"; DestDir: "{commoncf}\MTS-ESP"; Flags: ignoreversion uninsneveruninstall
Source: "{#MtsEspDir}\MTS-ESP.conf"; DestDir: "{commoncf}\MTS-ESP"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppName}\{#MyAppExeName}"
Name: "{autoprograms}\{#MyAppControllerName}"; Filename: "{app}\{#MyAppControllerName}\{#MyAppControllerExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppName}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autodesktop}\{#MyAppControllerName}"; Filename: "{app}\{#MyAppControllerName}\{#MyAppControllerExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppName}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
