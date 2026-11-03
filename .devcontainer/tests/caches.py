from pathlib import Path

homes=[Path('/root'),*Path('/home').iterdir()]
cache_dirs=[Path('/var/cache/apt'),Path('/var/lib/apt/lists'),Path('/usr/local/share/nvm/.cache'),Path('/tmp/tmp-k9s')]
for home in homes:
    cache_dirs.extend([home/'.cache/pip',home/'.npm'])
remaining=[]
for directory in cache_dirs:
    if directory.exists():
        remaining.extend(str(p) for p in directory.rglob('*') if p.is_file() and p.stat().st_size > 0)
assert not remaining, 'Package/install cache files remain: '+', '.join(remaining[:20])
print('PASS: apt, pip, npm, Node/NVM and k9s download caches are empty')
