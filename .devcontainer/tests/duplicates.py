"""Reject shadowed tool installations, while accepting aliases to the same inode."""
import collections
from importlib.metadata import distributions
import json
import os
from pathlib import Path
import subprocess

commands=['dig','nslookup','host','elasticdump','multielasticdump','ssh','scp','sftp','ssh-agent','ssh-keygen','git','node','npm','python','python3','pip','pip3','docker','kubectl','helm',
          'editorconfig-checker','minikube','k9s','gilt','claude','ec','ansible','ansible-lint','molecule']
directories=[Path(p) for p in ['/usr/local/bin','/usr/local/sbin','/usr/bin','/usr/sbin',
                              '/bin','/sbin','/home/vscode/.local/bin','/root/.local/bin']]
failures=[]
for command in commands:
    files={}
    for directory in directories:
        if not os.access(directory,os.X_OK):continue
        p=directory/command
        if p.is_file() and os.access(p,os.X_OK):
            info=p.stat();files.setdefault((info.st_dev,info.st_ino),[]).append(str(p))
    if len(files)>1:failures.append({command:list(files.values())})
assert not failures,'Duplicate/shadowed executables: '+json.dumps(failures)
packages=collections.defaultdict(set)
for dist in distributions():
    name=dist.metadata['Name'].lower().replace('_','-')
    packages[name].add((dist.version,str(dist._path.resolve())))
duplicates={name:sorted(rows) for name,rows in packages.items() if len(rows)>1}
assert not duplicates,'Duplicate Python distributions: '+json.dumps(duplicates)
for package in ['git-man','nodejs','npm','python3','python3-minimal','docker.io','moby-engine','slirp4netns','libslirp0']:
    result=subprocess.run(['dpkg-query','-W','-f=${db:Status-Status}',package],capture_output=True,text=True)
    assert result.stdout.strip()!='installed','Unexpected parallel distro package: '+package
print('PASS: no shadowed tool installations, duplicate Python distributions or parallel distro language packages')
