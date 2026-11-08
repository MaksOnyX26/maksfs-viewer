# Installs tools only on a disposable GitHub-hosted runner.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_ENVIRONMENT -ne 'github-hosted') {
    throw 'This preparation script is restricted to GitHub-hosted Actions runners.'
}

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Executable exited with $LASTEXITCODE" }
}

$venv = Join-Path $env:RUNNER_TEMP 'maksfs-tools'
Invoke-Checked python @('-m', 'venv', $venv)
$python = Join-Path $venv 'Scripts/python.exe'
Invoke-Checked $python @('-m', 'pip', 'install', '--require-hashes', '--only-binary=:all:', '--index-url', 'https://pypi.org/simple', '--retries', '2', '--timeout', '30', '-r', "$PSScriptRoot/windows-tools.lock")
Invoke-Checked $python @('-m', 'pip', 'check')
"$venv/Scripts" >> $env:GITHUB_PATH
"MAKSFS_PYTHON=$python" >> $env:GITHUB_ENV

# Fail closed if the official installer changes; update this hash only after review.
$installer = Join-Path $env:RUNNER_TEMP 'cygwin-setup.exe'
Invoke-WebRequest 'https://cygwin.com/setup-x86_64.exe' -OutFile $installer -TimeoutSec 90
$expected = '9d31ffc08b14eaaf5ddf15799a934f6bc1be3d87ed986736cb1980c508ed9502'
if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'Cygwin installer checksum changed. Review the official download before updating the pin.'
}
$cache = Join-Path $env:RUNNER_TEMP 'cygwin-downloads'
$arguments = @('--quiet-mode', '--no-admin', '--no-desktop', '--no-shortcuts', '--root', 'C:\cygwin64', '--local-package-dir', ('"' + $cache + '"'), '--site', 'https://mirrors.kernel.org/sourceware/cygwin/', '--packages', 'bash,patch,coreutils,tar,gzip,bzip2,xz,unzip,diffutils,findutils,sed,gawk,grep,which')
$process = Start-Process -FilePath $installer -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
if ($process.ExitCode -ne 0) { throw "Cygwin setup exited with $($process.ExitCode)" }

# Candidate variables snapshot at or before the viewer release commit, not mutable master.
$variables = Join-Path $env:RUNNER_TEMP 'maksfs-build-variables'
Invoke-WebRequest 'https://raw.githubusercontent.com/FirestormViewer/fs-build-variables/c17312d38377c003977cf5b6dcc83c6042eba194/variables' -OutFile $variables -TimeoutSec 60
"AUTOBUILD_VARIABLES_FILE=$variables" >> $env:GITHUB_ENV

'## Installed tools (not a viewer build)' >> $env:GITHUB_STEP_SUMMARY
"Cygwin installer SHA256: $expected" >> $env:GITHUB_STEP_SUMMARY
'Build variables candidate: c17312d38377c003977cf5b6dcc83c6042eba194' >> $env:GITHUB_STEP_SUMMARY
'Cygwin package versions come from the signed current mirror; see verification output. They are not fully locked.' >> $env:GITHUB_STEP_SUMMARY
