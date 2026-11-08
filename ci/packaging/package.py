"""Validate the staged tree, create portable ZIP and a file-listed NSIS installer."""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import os
import shutil
import struct
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'package-work/MaksFS'
OUT = ROOT / 'dist'

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

@lru_cache(maxsize=None)
def pe(path):
    b = path.read_bytes()
    if b[:2] != b'MZ':
        raise ValueError(f'Not PE: {path}')
    p = struct.unpack_from('<I', b, 0x3c)[0]
    if b[p:p+4] != b'PE\0\0':
        raise ValueError(f'Invalid PE: {path}')
    machine, n = struct.unpack_from('<HH', b, p+4)
    size = struct.unpack_from('<H', b, p+20)[0]
    o = p+24
    magic = struct.unpack_from('<H', b, o)[0]
    dd = o + (112 if magic == 0x20b else 96)
    sections = []
    for i in range(n):
        s = o+size+40*i
        vsize, va, rawsize, raw = struct.unpack_from('<IIII', b, s+8)
        sections.append((va, max(vsize, rawsize), raw))
    def offset(rva):
        for va, sz, raw in sections:
            if va <= rva < va+sz:
                return raw+rva-va
        raise ValueError(f'Unmapped RVA {rva:x}: {path}')
    def string(rva):
        q = offset(rva)
        return b[q:b.index(b'\0', q)].decode('ascii').lower()
    normal, delayed = [], []
    for index, step, target in [(1,20,normal),(13,32,delayed)]:
        rva, sz = struct.unpack_from('<II', b, dd+8*index)
        if not rva:
            continue
        q = offset(rva)
        for _ in range(sz//step):
            row = struct.unpack_from('<'+'I'*(step//4), b, q)
            if not any(row):
                break
            if index == 13:
                if not row[0] & 1:
                    raise ValueError('Legacy delay import addressing not supported')
                target.append(string(row[1]))
            else:
                target.append(string(row[3]))
            q += step
    return machine, normal, delayed

def nsi_quote(s):
    return str(s).replace('$', '$$').replace('"', '$\\"')

def main():
    OUT.mkdir(exist_ok=True)
    required = ['MaksFS.exe','slplugin.exe','llwebrtc.dll','msvcp140.dll','vcruntime140.dll',
      'licenses.txt','featuretable.txt','ca-bundle.crt','build_data.json',
      'app_settings/settings.xml','app_settings/message_template.msg',
      'skins/skins.xml','llplugin/media_plugin_cef.dll','llplugin/media_plugin_libvlc.dll',
      'llplugin/libcef.dll','llplugin/dullahan_host.exe','llplugin/libvlc.dll',
      'llplugin/libvlccore.dll','llplugin/icudtl.dat','llplugin/resources.pak',
      'llplugin/locales/en-US.pak','llplugin/locales/ru.pak']
    for name in required:
        p = STAGE / name
        if not p.is_file() or not p.stat().st_size:
            raise RuntimeError(f'Missing required file: {name}')
    for name in ['app_settings/shaders','character','fonts','llplugin/plugins']:
        if not any(p.is_file() for p in (STAGE/name).rglob('*')):
            raise RuntimeError(f'Empty resource directory: {name}')
    dependencies, missing = [], []
    system = Path(os.environ['SystemRoot']) / 'System32'
    for f in sorted(STAGE.rglob('*')):
        if f.suffix.lower() not in {'.exe','.dll'}:
            continue
        machine, imports, delayed = pe(f)
        # Third-party legacy Growl DLLs may be x86; record them, but require x64
        # for every core executable and active media/voice component.
        if (f.name.lower() in {'maksfs.exe','slplugin.exe','llwebrtc.dll','dullahan_host.exe',
                'media_plugin_cef.dll','media_plugin_libvlc.dll','libcef.dll','libvlc.dll','libvlccore.dll'}) and machine != 0x8664:
            raise RuntimeError(f'Wrong core architecture: {f}')
        rows = []
        for dep in imports:
            locations = [f.parent/dep, STAGE/dep, STAGE/'llplugin'/dep]
            packaged = next((p for p in locations if p.is_file()), None)
            if packaged:
                resolution = str(packaged.relative_to(STAGE))
                if pe(packaged)[0] != machine:
                    missing.append(f'{f.relative_to(STAGE)} -> architecture mismatch: {dep}')
            elif dep.startswith(('api-ms-win-','ext-ms-win-')):
                resolution = 'Windows API set'
            elif (system/dep).is_file() and not dep.startswith(('msvcp','vcruntime','msvcr','concrt')):
                resolution = 'Windows system DLL (runner); Windows 11 smoke test pending'
            else:
                resolution = 'MISSING'
                missing.append(f'{f.relative_to(STAGE)} -> {dep}')
            rows.append({'name':dep, 'resolved':resolution})
        dependencies.append({'file':f.relative_to(STAGE).as_posix(), 'machine':hex(machine),
                             'imports':rows, 'delay_imports':delayed})
    report = {'source': json.loads((ROOT/'packaging-inputs.json').read_text()),
        'required_files':required, 'dependencies':dependencies, 'missing':missing,
        'runtime_test':'Not performed: requires interactive Windows 11 with GPU and SL login',
        'profile':'ReleaseFS_open; FMOD, KDU, Havok, OpenSim, signing and updater disabled'}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if missing:
        raise RuntimeError('\n'.join(missing))
    version = (ROOT/'build-vc170-64/newview/viewer_version.txt').read_text().strip()
    binary_sha = report['source']['source_sha']
    for source in ['LICENSE','doc/LICENSE-source.txt','doc/LGPL-license.txt','doc/LICENSE-logos.txt']:
        shutil.copy2(ROOT/source, STAGE/Path(source).name)
    readme = f'''MaksFS {version} — Windows x64 experimental build\n
Based on Firestorm. This is not an official Firestorm release.
Source: https://github.com/MaksOnyX26/maksfs-viewer/tree/{binary_sha}
Profile: ReleaseFS_open. FMOD, KDU, Havok and OpenSim are disabled.
Performance improvements have not yet been implemented or measured.
The EXE is unsigned. Windows 11 interactive/GPU/login/voice/media tests are pending.

PORTABLE: Extract the entire ZIP into a writable folder and run MaksFS-Portable.cmd.
Settings, cache and logs are redirected to the data folder beside this launcher.
Do not start MaksFS.exe directly when you want portable data storage.
Do not place the portable folder in Program Files. Close the viewer before moving it.
Never share your data folder: it can contain account details and chat history.

INSTALLER: Installs for the current user, without administrator privileges.
Start from the MaksFS Experimental shortcut. Its profile is kept separate under
LocalAppData\\MaksFS-Experimental-Data. Uninstall preserves user data.

VC++ runtime DLLs are included app-local; no separate Python/Java installation needed.
Windows components, graphics drivers, network access and an SL account remain required.
OpenAL audio and all interactive features need runtime verification.
'''
    (STAGE/'README-MaksFS.txt').write_text(readme,encoding='utf-8')
    launcher = '''@echo off
setlocal
cd /d "%~dp0"
set "APPDATA=%~dp0data\\Roaming"
set "LOCALAPPDATA=%~dp0data\\Local"
if not exist "%APPDATA%" mkdir "%APPDATA%"
if not exist "%LOCALAPPDATA%" mkdir "%LOCALAPPDATA%"
if not exist "%APPDATA%" exit /b 1
if not exist "%LOCALAPPDATA%" exit /b 1
start "" /wait "%~dp0MaksFS.exe" %*
exit /b %errorlevel%
'''
    (STAGE/'MaksFS-Portable.cmd').write_bytes(launcher.replace('\n','\r\n').encode())
    installed = launcher.replace('set "APPDATA=%~dp0data\\Roaming"',
        'set "MAKSFS_PROFILE=%LOCALAPPDATA%\\MaksFS-Experimental-Data"\nset "APPDATA=%MAKSFS_PROFILE%\\Roaming"').replace(
        'set "LOCALAPPDATA=%~dp0data\\Local"','set "LOCALAPPDATA=%MAKSFS_PROFILE%\\Local"')
    (STAGE/'MaksFS.cmd').write_bytes(installed.replace('\n','\r\n').encode())
    files = sorted(p for p in STAGE.rglob('*') if p.is_file())
    hashes = {p.relative_to(STAGE).as_posix():sha(p) for p in files}
    (OUT/'file-manifest.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    name = f'MaksFS-{version}-Windows-x64'
    portable = OUT/(name+'-Portable.zip')
    with zipfile.ZipFile(portable,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:
            z.write(p, 'MaksFS/'+p.relative_to(STAGE).as_posix())
    with zipfile.ZipFile(portable) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(files)
        for relative,digest in hashes.items():
            assert hashlib.sha256(z.read('MaksFS/'+relative)).hexdigest() == digest
    lines = [
        'Unicode true', '!include "MUI2.nsh"', '!include "x64.nsh"',
        'Name "MaksFS Experimental"', f'OutFile "{nsi_quote(OUT/(name+"-Setup.exe"))}"',
        'InstallDir "$LOCALAPPDATA\\Programs\\MaksFS-Experimental"',
        'RequestExecutionLevel user', 'SetCompressor /SOLID lzma',
        '!insertmacro MUI_PAGE_WELCOME',
        f'!insertmacro MUI_PAGE_LICENSE "{nsi_quote(STAGE/"LGPL-license.txt")}"',
        '!insertmacro MUI_PAGE_DIRECTORY', '!insertmacro MUI_PAGE_INSTFILES',
        '!insertmacro MUI_PAGE_FINISH', '!insertmacro MUI_UNPAGE_CONFIRM',
        '!insertmacro MUI_UNPAGE_INSTFILES', '!insertmacro MUI_LANGUAGE "English"',
        'Function .onInit', '${IfNot} ${RunningX64}',
        'MessageBox MB_ICONSTOP "Windows x64 is required."', 'Abort', '${EndIf}',
        'SetShellVarContext current', 'FunctionEnd', 'Section "MaksFS"',
        'SetRegView 64']
    previous = None
    for p in files:
        rel = p.relative_to(STAGE)
        parent = str(rel.parent).replace('/','\\')
        if parent != previous:
            lines.append('SetOutPath "$INSTDIR'+('' if parent=='.' else '\\'+nsi_quote(parent))+'"')
            previous = parent
        lines.append(f'File "{nsi_quote(p)}"')
    key = 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MaksFS-Experimental'
    lines += ['SetOutPath "$INSTDIR"','WriteUninstaller "$INSTDIR\\Uninstall.exe"',
        'CreateShortcut "$SMPROGRAMS\\MaksFS Experimental.lnk" "$INSTDIR\\MaksFS.cmd" "" "$INSTDIR\\MaksFS.exe"',
        f'WriteRegStr HKCU "{key}" "DisplayName" "MaksFS Experimental"',
        f'WriteRegStr HKCU "{key}" "DisplayVersion" "{version}"',
        f'WriteRegStr HKCU "{key}" "UninstallString" \'$\\"$INSTDIR\\Uninstall.exe$\\"\'',
        'SectionEnd','Section "Uninstall"','SetShellVarContext current','SetRegView 64']
    for p in files:
        rel = str(p.relative_to(STAGE)).replace('/','\\')
        lines.append(f'Delete "$INSTDIR\\{nsi_quote(rel)}"')
    dirs = {str(p.parent.relative_to(STAGE)).replace('/','\\') for p in files}
    for p in files:
        dirs.update(str(d.relative_to(STAGE)).replace('/','\\') for d in p.parents if d!=STAGE and STAGE in d.parents)
    for d in sorted(dirs,key=lambda d:(d.count('\\'),len(d)),reverse=True):
        if d!='.': lines.append(f'RMDir "$INSTDIR\\{nsi_quote(d)}"')
    lines += ['Delete "$INSTDIR\\Uninstall.exe"','RMDir "$INSTDIR"',
        'Delete "$SMPROGRAMS\\MaksFS Experimental.lnk"',f'DeleteRegKey HKCU "{key}"','SectionEnd']
    script = ROOT/'package-work/MaksFS.nsi'
    script.write_text('\n'.join(lines),encoding='utf-8-sig')
    nsis = Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'NSIS/makensis.exe'
    subprocess.run([str(nsis),'/V2',str(script)],check=True)
    checksums = '\n'.join(f'{sha(p)}  {p.name}' for p in sorted(OUT.iterdir()) if p.suffix in {'.zip','.exe','.json'})+'\n'
    (OUT/'SHA256SUMS.txt').write_text(checksums)
    print(checksums)

if __name__ == '__main__':
    main()
