# Smoke test for the Wilsonic Windows installer.
#
# It installs the given installer silently, checks that the six files landed
# where wilsonic.iss says, checks that an existing MTS-ESP.conf is left alone
# and a missing one is written, then uninstalls and checks that the shared
# MTS-ESP files stay behind. It needs an elevated prompt.
#
# With -UpgradeFrom it installs an older installer first, the v0.43 one for
# example, so that the install under test is an upgrade: there must be one
# Wilsonic entry under Apps afterwards, the older LIBMTS.dll must be replaced,
# and the uninstall must still leave the MTS-ESP files.
#
# It is meant for a throwaway machine: the CI runner or a VM. It ends by
# uninstalling Wilsonic, and on a machine with no MTS-ESP.conf it writes one
# of its own first, so do not run it on a machine whose Wilsonic install you
# care about.
#
# Usage (PowerShell):
#   release\windows\smoke-install.ps1 -Installer release\out\Wilsonic_Win64_v0.45.0-beta-unsigned.exe -Version 0.45.0-beta
#   release\windows\smoke-install.ps1 -Installer ... -Version ... -UpgradeFrom WilsonicInstaller64_0_43b.exe
param(
    [Parameter(Mandatory = $true)][string]$Installer,
    [string]$Version = '',
    [string]$UpgradeFrom = '',
    [string]$MtsEspDir = (Join-Path $PSScriptRoot '..\mts-esp')
)
$ErrorActionPreference = 'Stop'

$script:failures = 0
function Check([string]$Description, [bool]$Condition) {
    if ($Condition) { Write-Host "  ok   $Description" }
    else { Write-Host "  FAIL $Description"; $script:failures++ }
}
function Sha([string]$Path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLower() }
function Run-Silently([string]$Exe, [string]$Log) {
    $arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-')
    if ($Log) { $arguments += "/LOG=`"$Log`"" }
    $process = Start-Process -FilePath $Exe -ArgumentList $arguments -Wait -PassThru
    return $process.ExitCode
}

$Installer = (Resolve-Path -LiteralPath $Installer).Path
$logDir = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { $env:TEMP }
$app = Join-Path $env:ProgramFiles 'Perfect Buzz Music\Wilsonic'
$vst3 = Join-Path $env:CommonProgramFiles 'VST3\Perfect Buzz Music'
$mts = Join-Path $env:CommonProgramFiles 'MTS-ESP'
$conf = Join-Path $mts 'MTS-ESP.conf'
$dll = Join-Path $mts 'LIBMTS.dll'
$uninstallKey = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{78427BB9-1C86-41AB-BC1F-53E7203BDCDD}_is1'
$installed = @(
    (Join-Path $app 'Wilsonic\Wilsonic.exe'),
    (Join-Path $app 'WilsonicController\WilsonicController.exe'),
    (Join-Path $vst3 'Wilsonic\Wilsonic.vst3'),
    (Join-Path $vst3 'WilsonicController\WilsonicController.vst3')
)

# An MTS-ESP.conf that was here before the test must come through untouched.
# On a clean machine, plant one so that the same thing can be checked.
$planted = $false
if (-not (Test-Path -LiteralPath $conf)) {
    New-Item -ItemType Directory -Force -Path $mts | Out-Null
    Set-Content -LiteralPath $conf -Value "# planted by smoke-install.ps1`nipc_support = 0" -NoNewline
    $planted = $true
}
$confBefore = Sha $conf

if ($UpgradeFrom) {
    $UpgradeFrom = (Resolve-Path -LiteralPath $UpgradeFrom).Path
    Write-Host "older install first: $UpgradeFrom"
    $rc = Run-Silently $UpgradeFrom (Join-Path $logDir 'wilsonic-install-0.log')
    Check "older installer exit code 0 (got $rc)" ($rc -eq 0)
    Check "older install left an uninstall entry under the same AppId" (Test-Path -LiteralPath $uninstallKey)
    if (Test-Path -LiteralPath $uninstallKey) {
        Write-Host "  older install shows version $((Get-ItemProperty -LiteralPath $uninstallKey).DisplayVersion)"
    }
    foreach ($f in $installed) { Check "older install wrote $f" (Test-Path -LiteralPath $f) }
    Check "the existing MTS-ESP.conf survived the older install" ((Sha $conf) -eq $confBefore)
    if (Test-Path -LiteralPath $dll) {
        $same = (Sha $dll) -eq (Sha (Join-Path $MtsEspDir 'Win\64bit\LIBMTS.dll'))
        Write-Host "  older install's LIBMTS.dll is $(if ($same) { 'the same as' } else { 'different from' }) the pinned build"
    }
}

Write-Host "first install, with an MTS-ESP.conf already present"
$log1 = Join-Path $logDir 'wilsonic-install-1.log'
$rc = Run-Silently $Installer $log1
Check "installer exit code 0 (got $rc)" ($rc -eq 0)
if ($rc -ne 0 -and (Test-Path $log1)) { Get-Content $log1 -Tail 40 }
foreach ($f in $installed) { Check "installed $f" (Test-Path -LiteralPath $f) }
Check "installed $dll" (Test-Path -LiteralPath $dll)
if (Test-Path -LiteralPath $dll) {
    Check "LIBMTS.dll is the pinned build" ((Sha $dll) -eq (Sha (Join-Path $MtsEspDir 'Win\64bit\LIBMTS.dll')))
}
Check "the existing MTS-ESP.conf was left alone" ((Sha $conf) -eq $confBefore)
Check "uninstall entry under the v0.43 AppId" (Test-Path -LiteralPath $uninstallKey)
if ($Version -and (Test-Path -LiteralPath $uninstallKey)) {
    $shown = (Get-ItemProperty -LiteralPath $uninstallKey).DisplayVersion
    Check "uninstall entry shows version $Version (got $shown)" ($shown -eq $Version)
}
$entries = @(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*', 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -like 'Wilsonic*' })
Check "one Wilsonic entry under Apps (found $($entries.Count))" ($entries.Count -eq 1)

if ($planted) {
    Write-Host "second install, with no MTS-ESP.conf"
    Remove-Item -LiteralPath $conf
    $rc = Run-Silently $Installer (Join-Path $logDir 'wilsonic-install-2.log')
    Check "installer exit code 0 (got $rc)" ($rc -eq 0)
    Check "MTS-ESP.conf was written" (Test-Path -LiteralPath $conf)
    if (Test-Path -LiteralPath $conf) {
        Check "MTS-ESP.conf is the pinned file" ((Sha $conf) -eq (Sha (Join-Path $MtsEspDir 'MTS-ESP.conf')))
    }
}

Write-Host "uninstall"
$uninstaller = Join-Path $app 'unins000.exe'
Check "uninstaller present" (Test-Path -LiteralPath $uninstaller)
if (Test-Path -LiteralPath $uninstaller) {
    $rc = Run-Silently $uninstaller ''
    Check "uninstaller exit code 0 (got $rc)" ($rc -eq 0)
    # The uninstaller finishes from a temporary copy; give it a moment.
    for ($i = 0; $i -lt 30 -and (Test-Path -LiteralPath $installed[0]); $i++) { Start-Sleep -Seconds 1 }
    foreach ($f in $installed) { Check "removed $f" (-not (Test-Path -LiteralPath $f)) }
    Check "LIBMTS.dll stays for other MTS-ESP plugins" (Test-Path -LiteralPath $dll)
    Check "MTS-ESP.conf stays" (Test-Path -LiteralPath $conf)
    Check "uninstall entry removed" (-not (Test-Path -LiteralPath $uninstallKey))
}

Write-Host ""
if ($script:failures -gt 0) {
    Write-Host "$($script:failures) check(s) failed"
    exit 1
}
Write-Host "all checks passed"
