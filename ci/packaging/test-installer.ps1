$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$installer = @(Get-ChildItem dist/*-Setup.exe)
if ($installer.Count -ne 1) { throw 'Expected exactly one installer' }
$target = Join-Path $env:RUNNER_TEMP 'MaksFS installer test'
if (Test-Path $target) { throw 'Test path already exists; refusing to overwrite' }
# NSIS /D must be the final argument, without quotes, including paths with spaces.
$p = Start-Process $installer[0].FullName -ArgumentList "/S /D=$target" -Wait -PassThru
if ($p.ExitCode -ne 0) { throw "Installer failed: $($p.ExitCode)" }
$manifest = Get-Content dist/file-manifest.json -Raw | ConvertFrom-Json -AsHashtable
foreach ($relative in $manifest.Keys) {
    $file = Join-Path $target $relative
    if (!(Test-Path -LiteralPath $file -PathType Leaf)) { throw "Installer omitted $relative" }
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest[$relative]) {
        throw "Installed file differs: $relative"
    }
}
# The uninstall must not recursively erase user-added files.
$sentinel = Join-Path $target 'keep-user-data.txt'
'preserve me' | Set-Content $sentinel
$p = Start-Process (Join-Path $target 'Uninstall.exe') -ArgumentList "/S _?=$target" -Wait -PassThru
if ($p.ExitCode -ne 0) { throw "Uninstaller failed: $($p.ExitCode)" }
if (!(Test-Path $sentinel)) { throw 'Uninstaller removed unknown/user data' }
foreach ($relative in $manifest.Keys) {
    if (Test-Path -LiteralPath (Join-Path $target $relative)) { throw "Uninstaller left packaged file: $relative" }
}
"PASS: silent install to a path with spaces; all $($manifest.Count) files match SHA256; uninstall removed packaged files and preserved user-added data. Interactive Windows 11 viewer test remains pending." | Set-Content dist/installer-test.txt
