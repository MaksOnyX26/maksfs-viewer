"""Persist packaging inputs before packaging, excluding compiler intermediates."""
from pathlib import Path
import json
import os
import zipfile

root = Path(__file__).resolve().parents[2]
build = root / 'build-vc170-64'
assert (build / 'newview/Release/firestorm-bin.exe').is_file()
out = root / 'ci-snapshot'
out.mkdir(exist_ok=True)
selected = ['packages', 'sharedlibs/Release', 'newview/Release',
            'llplugin/slplugin/Release', 'media_plugins/cef/Release',
            'media_plugins/libvlc/Release', 'newview/viewer_version.txt',
            'newview/packages-info.txt', 'packages-info.txt', 'CMakeCache.txt']
with zipfile.ZipFile(out / 'packaging-inputs.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as z:
    for name in selected:
        p = build / name
        for f in ([p] if p.is_file() else sorted(p.rglob('*'))):
            if f.is_file() and f.suffix.lower() not in {'.obj', '.lib', '.pdb', '.ilk', '.pch', '.tlog', '.idb'}:
                z.write(f, f.relative_to(root).as_posix())
    z.writestr('packaging-inputs.json', json.dumps({'source_sha': os.environ['GITHUB_SHA'],
        'run_id': os.environ['GITHUB_RUN_ID'], 'profile': 'ReleaseFS_open',
        'original_successful_run': 42509539984}, indent=2))
print(out / 'packaging-inputs.zip')
