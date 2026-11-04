import os
from pathlib import Path
from shutil import which

managers=['nvm','fnm','n','nodenv','nvs','volta','asdf','mise','pyenv','uv','rye',
          'conda','mamba','micromamba','rbenv','rvm','gvm','rustup','sdk','jenv',
          'corepack','yarn','yarnpkg','pnpm','pnpx']
assert not [name for name in managers if which(name)], 'Unexpected version manager/dispatcher on PATH'
homes=[Path('/home/vscode')]
if os.geteuid()==0:
    homes.append(Path('/root'))
for prefix in homes:
    for name in ['.nvm','.fnm','.volta','.asdf','.local/share/mise','.pyenv',
                 '.rye','.rbenv','.rvm','.gvm','.rustup','.sdkman']:
        assert not (prefix/name).exists(), f'Unexpected manager installation: {prefix/name}'
for directory in ['/usr/local/share/nvm','/usr/local/lib/node_modules/n',
                  '/usr/local/lib/node_modules/corepack','/opt/conda','/opt/pyenv','/opt/asdf']:
    assert not Path(directory).exists(), f'Unexpected manager installation: {directory}'
assert 'NVM_DIR' not in os.environ
assert 'NVM_SYMLINK_CURRENT' not in os.environ
assert which('node')=='/usr/local/bin/node'
assert which('npm')=='/usr/local/bin/npm'
assert which('npx')=='/usr/local/bin/npx'
assert not Path('/usr/bin/python3').exists(), 'Unexpected second/system Python'
assert not list(Path('/usr/local/bin').glob('python3.7*'))
print('PASS: direct Node/npm/npx, one Python 3.12, no runtime version managers or Corepack')
