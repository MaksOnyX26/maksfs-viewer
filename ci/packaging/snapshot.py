"""Persist packaging inputs before packaging, excluding compiler intermediates."""
from pathlib import Path
import json
import os
import zipfile
import subprocess

root = Path(__file__).resolve().parents[2]
build = root / 'build-vc170-64'
assert (build / 'newview/Release/firestorm-bin.exe').is_file()
source_sha = os.environ.get('SOURCE_SHA', os.environ['GITHUB_SHA'])
actual_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
if actual_sha != source_sha:
    raise RuntimeError(f'Unexpected build checkout: {actual_sha}; expected {source_sha}')
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
    z.writestr('packaging-inputs.json', json.dumps({'source_sha': source_sha,
        'workflow_sha': os.environ.get('WORKFLOW_SHA', os.environ['GITHUB_SHA']),
        'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
        'run_url': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
        'run_id': os.environ['GITHUB_RUN_ID'], 'profile': 'ReleaseFS_open',
        'fresh_compile': True}, indent=2))
print(out / 'packaging-inputs.zip')
