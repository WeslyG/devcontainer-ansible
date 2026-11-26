"""Prefetch the large universal Ansible wheel; pip verifies every committed hash."""
import json
from pathlib import Path
import re
import subprocess
import tempfile

lock=Path('/tmp/requirements.txt')
version=re.search(r'^ansible==([^\s\\]+)',lock.read_text(),re.M)[1]
curl=['curl','--fail','--silent','--show-error','--location','--connect-timeout','15','--max-time','240','--retry','2']
metadata=json.loads(subprocess.check_output([*curl,f'https://pypi.org/pypi/ansible/{version}/json']))
wheel=next(row for row in metadata['urls'] if row['filename']==f'ansible-{version}-py3-none-any.whl')
with tempfile.TemporaryDirectory(prefix='ansible-wheel-') as temporary:
    target=Path(temporary)/wheel['filename']
    # A distinct CDN key avoids an indefinitely slow cached streaming response.
    subprocess.run([*curl,wheel['url']+'?ansible-infra-wheel=1','--output',str(target)],check=True)
    subprocess.run(['python','-m','pip','install','--no-cache-dir','--no-compile','--require-hashes',
                    '--find-links',temporary,'-r',str(lock)],check=True)
subprocess.run(['python','-m','pip','check'],check=True)
