"""Automatic dated image tags. Reads registry tags; never publishes anything."""
import argparse
from datetime import datetime
import os
import re
from zoneinfo import ZoneInfo
from common import fetch

REPOSITORY='weslyg/ansible-infra'
VERSION_PATTERN=r'\d{4}\.\d{2}\.\d{2}(?:-[1-9]\d*)?'

def validate(value):
    if not re.fullmatch(VERSION_PATTERN,value):raise ValueError('Expected YYYY.MM.DD or YYYY.MM.DD-N (N >= 1)')
    datetime.strptime(value.split('-')[0],'%Y.%m.%d')
    return value

def choose(day,tags):
    datetime.strptime(day,'%Y.%m.%d')
    pattern=re.compile(r'ansible(?:10|12|14)-'+re.escape(day)+r'(?:-([1-9]\d*))?')
    used=[int(m[1] or 0) for tag in tags if (m:=pattern.fullmatch(tag))]
    return day if not used else f'{day}-{max(used)+1}'

def registry_tags(day):
    # Docker Hub's public API, filtered by each image family; consume every page.
    tags=[]
    for major in ['10','12','14']:
        url=f'https://hub.docker.com/v2/repositories/{REPOSITORY}/tags?page_size=100&name=ansible{major}-{day}'
        while url:
            if not url.startswith(f'https://hub.docker.com/v2/repositories/{REPOSITORY}/tags'):
                raise ValueError('Unexpected registry pagination URL')
            data=fetch(url);tags.extend(row['name'] for row in data['results']);url=data.get('next')
    return tags

def select(check_registry=False):
    day=datetime.now(ZoneInfo('Asia/Yekaterinburg')).strftime('%Y.%m.%d')
    import subprocess
    tags=subprocess.check_output(['docker','image','ls','--format','{{.Tag}}','ansible-infra'],text=True).splitlines()
    if check_registry:tags+=registry_tags(day)
    return choose(day,tags)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check-registry',action='store_true');parser.add_argument('--github-env',action='store_true')
    args=parser.parse_args();value=select(args.check_registry)
    if args.github_env:
        with open(os.environ['GITHUB_ENV'],'a') as stream:stream.write(f'PLATFORM_VERSION={value}\nTAG_VERSION={value}\n')
    print(value)
