from pathlib import Path
import subprocess
import tempfile
import json
manifest=json.loads(Path('/repo/images.json').read_text())
version=manifest['tools']['openssh']['version']
banner=subprocess.check_output(['ssh','-V'],stderr=subprocess.STDOUT,text=True)
assert 'OpenSSH_'+version in banner,banner
assert subprocess.check_output(['dpkg-query','-W','-f=${Version}','openssh-client'],text=True)=='1:'+version
assert not Path('/usr/local/sbin/sshd').exists() and not Path('/usr/sbin/sshd').exists()
with tempfile.TemporaryDirectory() as temporary:
    key=Path(temporary)/'id_ed25519'
    subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(key)],check=True)
    subprocess.run(['ssh-keygen','-lf',str(key)+'.pub'],check=True)
    result=subprocess.check_output(['ssh','-G','-o','BatchMode=yes','localhost'],text=True)
    assert 'batchmode yes' in result
print('PASS: pinned OpenSSH client, key generation and config parsing; no SSH server')
