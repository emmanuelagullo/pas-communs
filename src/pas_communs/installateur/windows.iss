#define AppVersion "@@VERSION@@"
#define OutputDir "@@SORTIE@@"

[Setup]
AppId=@@APP_ID@@
AppName=@@NOM@@
AppVersion={#AppVersion}
AppPublisher=@@NOM@@
AppPublisherURL=@@URL@@
DefaultDirName={localappdata}\Programs\@@PROGRAMME@@\app
DefaultGroupName=@@NOM@@
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
UsePreviousAppDir=yes
OutputDir={#OutputDir}
OutputBaseFilename=@@PROGRAMME@@-Setup-{#AppVersion}-x64
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
WizardStyle=modern
UninstallDisplayName=@@NOM@@
; Les données résident dans {localappdata}\@@DONNEES@@.
; Ne jamais ajouter de directive [UninstallDelete] sur ce dossier.

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
Source: "@@SOURCE@@\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
; Le même nom que le raccourci #L7 remplace son point d'entrée.
Name: "{userprograms}\@@NOM@@"; Filename: "{app}\@@PROGRAMME@@.exe"; WorkingDir: "{app}"
Name: "{group}\Désinstaller @@NOM@@"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\@@PROGRAMME@@.exe"; Description: "Ouvrir @@NOM@@"; Flags: postinstall nowait skipifsilent

[Code]
function InitializeSetup: Boolean;
var
  VersionInstallee: String;
begin
  Result := True;
  if WizardSilent then
    Exit;
  if RegQueryStringValue(HKCU,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\@@APP_ID@@_is1',
    'DisplayVersion', VersionInstallee) then
    Result := MsgBox(
      '@@NOM_PASCAL@@ ' + VersionInstallee + ' est déjà installé pour ce compte.' + #13#10 + #13#10 +
      'Installer la version {#AppVersion} à sa place ?' + #13#10 +
      'Les données et vos sauvegardes seront conservées.' + #13#10 +
      'Fermez @@NOM_PASCAL@@ avant de continuer.',
      mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
end;

function WebView2Detecte: Boolean;
var
  Version: String;
begin
  // Détection documentée par Microsoft ; un indice, jamais un blocage de l'installation.
  Result :=
    (RegQueryStringValue(HKLM32,
      'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
      'pv', Version) and (Version <> '') and (Version <> '0.0.0.0')) or
    (RegQueryStringValue(HKCU,
      'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
      'pv', Version) and (Version <> '') and (Version <> '0.0.0.0'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and (not WizardSilent) and (not WebView2Detecte) then
    MsgBox(
      '@@NOM_PASCAL@@ est installé, mais le composant Microsoft Edge WebView2 n’a pas été détecté.' + #13#10 + #13#10 +
      'S’il manque, la fenêtre de @@NOM_PASCAL@@ restera vide ou ne s’ouvrira pas. ' +
      'Téléchargez « Evergreen Bootstrapper » sur https://developer.microsoft.com/microsoft-edge/webview2/ ' +
      'puis relancez @@NOM_PASCAL@@. Si la fenêtre s’ouvre normalement, ignorez ce message.',
      mbInformation, MB_OK);
end;
