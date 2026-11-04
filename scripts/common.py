"""Shared repository utilities; standard library only on the host."""
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def read_json(path):
    return json.loads(Path(path).read_text())

def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')

def fetch(url, json_data=True):
    headers={'User-Agent': 'ansible-devcontainer-updater'}
    if 'api.github.com/' in url and os.environ.get('GITHUB_TOKEN'):
        headers['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers), timeout=90) as response:
        data=response.read().decode()
    return json.loads(data) if json_data else data

def run(args, **kwargs):
    print('+', ' '.join(map(str,args)), flush=True)
    return subprocess.run(list(map(str,args)), cwd=ROOT, check=True, **kwargs)

def jsonc(text):
    return json.loads(re.sub(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/', lambda m:m[1] or '', text, flags=re.S))

def matrix():
    return read_json(ROOT/'images.json')

def cli():
    return os.environ.get('DEVCONTAINER_CLI','devcontainer')

def config(major):
    return ROOT/f'.devcontainer/ansible{major}/devcontainer.json'

def image(major):
    return f'ansible-infra:ansible{major}-local'
