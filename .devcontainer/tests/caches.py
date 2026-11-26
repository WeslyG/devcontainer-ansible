from pathlib import Path

homes=[Path('/root'),*Path('/home').iterdir()]
cache_dirs=[Path('/var/cache/apt'),Path('/var/lib/apt/lists'),Path('/tmp/tmp-k9s')]
for home in homes:
    cache_dirs.extend([home/'.cache',home/'.npm',home/'go/pkg/mod',home/'.cargo/registry',home/'.cargo/git',home/'.minikube/cache',home/'.kube/cache'])
remaining=[]
for directory in cache_dirs:
    if directory.exists():
        remaining.extend(str(p) for p in directory.rglob('*') if p.is_file() and p.stat().st_size > 0)
assert not remaining, 'Package/install cache files remain: '+', '.join(remaining[:20])
bytecode=list(Path('/usr/local/lib').glob('**/__pycache__'))
assert not bytecode,'Python bytecode cache remains: '+str(bytecode[:10])
import shutil
assert shutil.which('go') is None and not Path('/usr/local/go').exists(),'Go build toolchain remains in runtime'
print('PASS: apt, pip, npm, installer download caches are empty')
