@echo off
setlocal
if not "%GITHUB_ACTIONS%"=="true" exit /b 2
if not "%RUNNER_ENVIRONMENT%"=="github-hosted" exit /b 2
if not defined MAKSFS_PYTHON exit /b 2
if not defined AUTOBUILD_VARIABLES_FILE exit /b 2
for %%I in ("%MAKSFS_PYTHON%") do set "PATH=%%~dpI;C:\cygwin64\bin;%PATH%"
set "PYTHON=%MAKSFS_PYTHON%"
for /f "usebackq tokens=*" %%I in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -version "[17.0,18.0)" -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "MAKSFS_VS=%%I"
if not defined MAKSFS_VS exit /b 2
call "%MAKSFS_VS%\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
if errorlevel 1 exit /b 2
if "%~1"=="configure" goto configure
if "%~1"=="compile" goto compile
exit /b 2

:configure
autobuild configure -A 64 -c ReleaseFS_open -- --chan MaksFS-Experimental --no-opensim --no-package -DINSTALL_PROPRIETARY:BOOL=OFF -DHAVOK:BOOL=OFF -DHAVOK_TPV:BOOL=OFF -DUSE_KDU:BOOL=OFF -DUSE_FMODSTUDIO:BOOL=OFF -DUSE_BUGSPLAT:BOOL=OFF -DRELEASE_CRASH_REPORTING:BOOL=OFF -DNON_RELEASE_CRASH_REPORTING:BOOL=OFF -DENABLE_SIGNING:BOOL=OFF -DUSE_VELOPACK:BOOL=OFF -DLL_TESTS:BOOL=OFF
exit /b %errorlevel%

:compile
cmake --build build-vc170-64 --config Release --parallel 1 -- /p:CL_MPCount=2 /fl /flp:"logfile=%GITHUB_WORKSPACE%\ci-logs\msbuild.log;verbosity=normal"
exit /b %errorlevel%
