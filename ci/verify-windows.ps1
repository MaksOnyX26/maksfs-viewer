$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_ENVIRONMENT -ne 'github-hosted') {
    throw 'Run this verification in GitHub-hosted Actions.'
}
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    $output = & $Executable @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "$Executable exited with ${LASTEXITCODE}: $output" }
    $output | Write-Output
}

$python = $env:MAKSFS_PYTHON
$scripts = Split-Path -Parent $python
# Put native Python/CMake first, then Cygwin, then the runner PATH.
$env:PATH = "$scripts;C:\cygwin64\bin;$env:PATH"
Invoke-Checked $python @('-c', 'import sys, struct; assert sys.version_info[:3] == (3,11,9); assert struct.calcsize("P") == 8; import llsd, llbase.config, pyzstd; assert pyzstd.decompress(pyzstd.compress(b"maksfs")) == b"maksfs"; print(sys.version)')
Invoke-Checked $python @('-m', 'pip', 'check')
Invoke-Checked $python @('-c', 'from importlib.metadata import version; assert version("autobuild") == "3.10.2"; assert version("cmake") == "4.1.2"; assert version("llbase") == "1.3.1"; assert version("llsd") == "1.2.4"; print("Pinned Python tools verified")')
Invoke-Checked (Join-Path $scripts 'cmake.exe') @('--version')
Invoke-Checked (Join-Path $scripts 'autobuild.exe') @('--version')
Invoke-Checked 'C:\cygwin64\bin\bash.exe' @('--noprofile', '--norc', '-c', 'set -eu; test -x /usr/bin/patch; /usr/bin/patch --version; /usr/bin/cygpath -w /; /usr/bin/cygcheck -c')

$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vs = @(Invoke-Checked $vswhere @('-products', '*', '-version', '[17.0,18.0)', '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'))
if (!$vs.Count) { throw 'Visual Studio 2022 C++ tools were not found' }
$msvcRoot = Join-Path $vs[0] 'VC/Tools/MSVC'
$compiler = @(Get-ChildItem -LiteralPath $msvcRoot -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'bin/Hostx64/x64/cl.exe') })
if (!$compiler.Count) { throw 'MSVC x64 compiler was not found' }
$sdkRoot = "${env:ProgramFiles(x86)}\Windows Kits\10"
$sdks = @(Get-ChildItem -LiteralPath "$sdkRoot/Include" -Directory | Where-Object {
    (Test-Path -LiteralPath (Join-Path $_.FullName 'um/Windows.h')) -and
    (Test-Path -LiteralPath "$sdkRoot/Lib/$($_.Name)/um/x64/kernel32.lib") -and
    (Test-Path -LiteralPath "$sdkRoot/bin/$($_.Name)/x64/rc.exe")
})
if (!$sdks.Count) { throw 'A complete Windows SDK with x64 libraries and resource compiler was not found' }
if (!(Test-Path -LiteralPath 'C:\Program Files (x86)\NSIS\makensis.exe')) { throw 'NSIS was not found' }
Invoke-Checked 'C:\Program Files (x86)\NSIS\makensis.exe' @('/VERSION')
if (!(Test-Path -LiteralPath $env:AUTOBUILD_VARIABLES_FILE)) { throw 'Build variables file was not downloaded' }
if (!(Select-String -LiteralPath $env:AUTOBUILD_VARIABLES_FILE -Pattern '^LL_BUILD_WINDOWS_RELEASEFS_OPEN=' -Quiet)) {
    throw 'Build variables do not define ReleaseFS_open for Windows'
}

'## Tool checks passed' >> $env:GITHUB_STEP_SUMMARY
"VS2022: $($vs[0]); MSVC versions: $($compiler.Name -join ', ')" >> $env:GITHUB_STEP_SUMMARY
"Complete SDK versions: $($sdks.Name -join ', ')" >> $env:GITHUB_STEP_SUMMARY
'Python 3.11.9 x64; CMake 4.1.2; autobuild 3.10.2; llbase 1.3.1; llsd 1.2.4; Cygwin/patch and NSIS checked.' >> $env:GITHUB_STEP_SUMMARY
'### Installed Python packages' >> $env:GITHUB_STEP_SUMMARY
Invoke-Checked $python @('-m', 'pip', 'freeze', '--all') | Tee-Object -FilePath $env:GITHUB_STEP_SUMMARY -Append
'This verifies tools only. Viewer libraries, compiler compatibility and runtime behavior still need a separately authorized build.' >> $env:GITHUB_STEP_SUMMARY
