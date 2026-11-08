"""Stage the existing build with Firestorm's full manifest; never compile."""
import os
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[2]
build = root / 'build-vc170-64'
cache = dict(re.findall(r'^([^/#:\n]+):[^=\n]+=(.*)$', (build / 'CMakeCache.txt').read_text(), re.M))
sys.path.insert(0, str(root / 'indra/newview'))
import viewer_manifest as vm

# Retain the complete upstream resource/dependency selection. Only the final
# installer step is replaced with our separately testable per-user installer.
vm.Windows_x86_64_Manifest.package_finish = lambda self: None
vm.Windows_x86_64_Manifest.final_exe = lambda self: 'MaksFS.exe'
stage = root / 'package-work/MaksFS'
stage.mkdir(parents=True, exist_ok=False)
os.chdir(build / 'newview')
opts = {
    'actions': 'copy package', 'platform': 'windows', 'arch': 'x86_64',
    'source': str(root / 'indra/newview'), 'artwork': str(root / 'indra/newview'),
    'build': str(build / 'newview'), 'dest': str(stage),
    'configuration': 'Release', 'buildtype': 'Release',
    'channel': cache['VIEWER_CHANNEL'], 'grid': 'agni',
    'viewer_flavor': cache.get('ND_VIEWER_FLAVOR', 'hvk'),
    'versionfile': str(build / 'newview/viewer_version.txt'),
}
extras = {'bugsplat': '', 'discord': cache.get('USE_DISCORD', 'OFF'),
          'openal': cache.get('USE_OPENAL', 'OFF'), 'fmodstudio': 'OFF',
          'tracy': cache.get('USE_TRACY', 'OFF'), 'avx2': 'OFF', 'velopack': 'OFF'}
sys.argv = [str(root / 'indra/newview/viewer_manifest.py')] + [f'--{k}={v}' for k,v in opts.items()]
vm.main(extra=[dict(name=k, description=k, default=v) for k,v in extras.items()])
