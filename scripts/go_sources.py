"""Shared source pins and targeted security module updates for native Go CLIs."""
import copy
import hashlib
import re
from common import download, fetch

MODULES=['github.com/containerd/containerd','github.com/containerd/containerd/v2',
         'github.com/go-git/go-git/v5','github.com/go-jose/go-jose/v4','github.com/klauspost/compress',
         'github.com/hashicorp/go-getter','golang.org/x/crypto','golang.org/x/mod','golang.org/x/net',
         'golang.org/x/text','google.golang.org/grpc','oras.land/oras-go/v2']

def compatible_containerd(versions,kubernetes_version,read_module):
    numbers=lambda value:tuple(map(int,value.removeprefix('v').split('.')))
    series={}
    for version in versions:
        if re.fullmatch(r'v2\.\d+\.\d+',version):
            key=numbers(version)[:2]
            if key not in series or numbers(version)>numbers(series[key]):series[key]=version
    for candidate in sorted(series.values(),key=numbers,reverse=True):
        source=read_module(candidate)
        required=re.findall(r'^\s*k8s.io/(?:api|apimachinery|client-go)\s+(v\d+\.\d+\.\d+)',source,re.M)
        if not required or max(numbers(v)[:2] for v in required)<=numbers(kubernetes_version)[:2]:return candidate
    raise ValueError('No compatible stable containerd series found')

def constrain_k9s(data):
    version=data['tools']['k9s']
    module=fetch(f'https://raw.githubusercontent.com/derailed/k9s/v{version}/go.mod',False)
    expected=re.search(r'^\s*k8s.io/kubectl\s+(v\d+\.\d+\.\d+)',module,re.M)
    if not expected:raise ValueError('Review K9s Kubernetes SDK compatibility')
    base='https://proxy.golang.org/github.com/containerd/containerd/v2/@v/'
    selected=compatible_containerd(fetch(base+'list',False).split(),expected[1],lambda v:fetch(base+v+'.mod',False))
    project=data['tools']['goSourceProjects']['k9s']
    project['moduleOverrides']={'github.com/containerd/containerd/v2':selected}
    project['compatibilityNote']=f'K9s uses Kubernetes SDK {expected[1]}; containerd {selected} is the latest compatible stable series patch'

def discover(data):
    data['tools']['goSecurityModules']={name:fetch('https://proxy.golang.org/'+name+'/@latest')['Version'] for name in MODULES}
    projects={}
    for name,repo,version in [('k9s','derailed/k9s',data['tools']['k9s']),
                              ('minikube','kubernetes/minikube',data['tools']['kubernetes']['minikube'])]:
        url=f'https://codeload.github.com/{repo}/tar.gz/refs/tags/v{version}'
        projects[name]={'repo':repo,'version':version,'url':url,'sha256':hashlib.sha256(download(url)).hexdigest()}
    version=data['tools']['kubernetes']['version']
    url=f'https://raw.githubusercontent.com/kubernetes/kubernetes/v{version}/cmd/kubectl/kubectl.go'
    projects['kubectl']={'repo':'kubernetes/kubernetes','version':version,'url':url,'sha256':hashlib.sha256(download(url)).hexdigest()}
    data['tools']['goSourceProjects']=projects
    constrain_k9s(data)

def configuration(data):
    projects=copy.deepcopy(data['tools']['goSourceProjects'])
    expected={'k9s':data['tools']['k9s'],'minikube':data['tools']['kubernetes']['minikube'],'kubectl':data['tools']['kubernetes']['version']}
    if any(projects[name]['version']!=version for name,version in expected.items()):
        raise ValueError('Canonical CLI version differs from pinned source release')
    modules=data['tools']['goSecurityModules']
    projects['k9s'].update(package='.',modules={name:value for name,value in modules.items() if name!='github.com/hashicorp/go-getter'})
    projects['k9s']['modules'].update(projects['k9s'].get('moduleOverrides',{}))
    projects['minikube'].update(package='./cmd/minikube',modules={name:modules[name] for name in [
        'github.com/go-jose/go-jose/v4','github.com/hashicorp/go-getter','golang.org/x/crypto',
        'golang.org/x/net','golang.org/x/text','google.golang.org/grpc']})
    projects['kubectl'].update(package='.',modules={name:modules[name] for name in ['golang.org/x/net','golang.org/x/text']})
    return {'projects':projects}

def sbom(data):
    tools=data['tools'];build=tools['giltBuild']
    rows=[('github.com/retr0h/gilt/v2','v'+tools['gilt']),
          ('github.com/editorconfig-checker/editorconfig-checker/v'+build['editorconfigVersion'].split('.')[0],'v'+build['editorconfigVersion']),
          ('github.com/derailed/k9s','v'+tools['k9s']),('k8s.io/minikube','v'+tools['kubernetes']['minikube']),
          ('k8s.io/kubectl','v0.'+tools['kubernetes']['version'].split('.',1)[1])]
    return {'bomFormat':'CycloneDX','specVersion':'1.6','version':1,'components':[
        {'type':'library','name':name,'version':version,'purl':f'pkg:golang/{name}@{version}','bom-ref':f'pkg:golang/{name}@{version}'} for name,version in rows]}
