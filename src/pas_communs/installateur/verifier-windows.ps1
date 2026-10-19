# Banc destructible sur runner CI uniquement. Aucun dossier métier existant n'est utilisé.
param([Parameter(Mandatory=$true)][string]$Configuration,
      [Parameter(Mandatory=$true)][string]$Setup,
      [Parameter(Mandatory=$true)][string]$Version)
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -and $env:GITLAB_CI -ne 'true') {
    throw 'Utiliser un runner CI jetable pour verifier le setup.'
}
$c = Get-Content -LiteralPath $Configuration -Raw -Encoding UTF8 | ConvertFrom-Json
$cle = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$($c.app_id)_is1"
$donnees = Join-Path $env:LOCALAPPDATA $c.donnees
if ((Test-Path $cle) -or (Test-Path $donnees)) {
    throw 'Installation ou donnees deja presentes : verification refusee.'
}
$preuve = Join-Path $donnees 'preuve-conservation-ci.txt'
New-Item -ItemType Directory -Path $donnees | Out-Null
Set-Content -LiteralPath $preuve -Value 'Donnees fictives a conserver' -Encoding UTF8
function Executer([string]$Fichier, [string[]]$Arguments) {
    $p = Start-Process -FilePath $Fichier -ArgumentList $Arguments -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw "Echec de $Fichier (code $($p.ExitCode))." }
}
function Conserver {
    if (!(Test-Path $preuve) -or (Get-Content $preuve -Raw).Trim() -ne 'Donnees fictives a conserver') {
        throw 'Les donnees fictives ont ete modifiees.'
    }
}
try {
    $options = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART')
    Executer $Setup $options
    if (!(Test-Path $cle)) { throw 'Entree Windows absente.' }
    $installation = Get-ItemProperty -Path $cle
    if ($installation.DisplayVersion -ne $Version) { throw 'Version Windows incorrecte.' }
    $dossier = $installation.InstallLocation
    $exe = Join-Path $dossier ($c.programme + '.exe')
    if (!(Test-Path $exe)) { throw 'Executable installe absent.' }
    $embarquee = Join-Path $dossier '_internal\version-application.txt'
    if ((Get-Content -LiteralPath $embarquee -Raw -Encoding UTF8).Trim() -ne $Version) {
        throw 'Version embarquee incorrecte.'
    }
    $raccourci = Join-Path ([Environment]::GetFolderPath('Programs')) ($c.nom + '.lnk')
    if (!(Test-Path $raccourci)) { throw 'Raccourci absent.' }
    $cible = (New-Object -ComObject WScript.Shell).CreateShortcut($raccourci).TargetPath
    if ($cible -ne $exe) { throw 'Cible du raccourci incorrecte.' }
    Executer $exe @('--verifier-distribution')
    Conserver
    Executer $Setup $options
    Executer $exe @('--verifier-distribution')
    Conserver
    Executer (Join-Path $dossier 'unins000.exe') $options
    if ((Test-Path $exe) -or (Test-Path $cle) -or (Test-Path $raccourci)) {
        throw 'Desinstallation incomplete.'
    }
    Conserver
    Write-Output 'Setup : installation, raccourci, controle, reinstallation et desinstallation avec conservation : OK'
} finally {
    # Seul le temoin cree par ce banc est retire, jamais un dossier de donnees.
    if (Test-Path $preuve) { Remove-Item -LiteralPath $preuve }
}
