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
