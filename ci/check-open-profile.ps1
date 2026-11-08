param([Parameter(Mandatory)][string]$CachePath)
$ErrorActionPreference = 'Stop'
$cache = Get-Content -LiteralPath $CachePath
$off = @('INSTALL_PROPRIETARY', 'HAVOK', 'HAVOK_TPV', 'USE_KDU', 'USE_FMODSTUDIO', 'USE_BUGSPLAT', 'RELEASE_CRASH_REPORTING', 'NON_RELEASE_CRASH_REPORTING', 'ENABLE_SIGNING', 'USE_VELOPACK', 'PACKAGE', 'OPENSIM', 'LL_TESTS', 'USE_AVX_OPTIMIZATION', 'USE_AVX2_OPTIMIZATION', 'USE_LTO')
foreach ($key in $off) {
    $entry = @($cache | Where-Object { $_ -match ('^' + $key + ':[^=]+=') })
    if ($entry.Count -ne 1 -or $entry[0] -notmatch '=(OFF|FALSE|NO|0)$') {
        throw "Open-profile guard failed: $key must explicitly be disabled"
    }
}
foreach ($entry in @('ADDRESS_SIZE:STRING=64', 'CMAKE_GENERATOR:INTERNAL=Visual Studio 17 2022', 'VIEWER_CHANNEL:STRING=Firestorm-MaksFS-Experimental')) {
    if ($cache -notcontains $entry) { throw "Unexpected build configuration: missing $entry" }
}
Write-Output 'Open-profile settings verified before compilation.'
