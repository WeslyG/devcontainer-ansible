"""Generate devcontainer variants from one template and images.json."""
import argparse
import copy
import json
import hashlib
import re
from common import ROOT, matrix, read_json

def generated():
    data=matrix()
    template=read_json(ROOT/'.devcontainer/template.json')
    result={}
    for major,variant in data['variants'].items():
        for default in ([False,True] if major==data['default'] else [False]):
            cfg=copy.deepcopy(template)
            cfg['name']=f'Ansible {major}'
            cfg['build']={'dockerfile':'Dockerfile' if default else '../Dockerfile','context':'..' if default else '../..','args':{
                'PYTHON_IMAGE':variant['pythonImage'], 'REQUIREMENTS_FILE':f'requirements/ansible{major}.txt',
                'ANSIBLE_MAJOR':major, 'GIT_BUILDER_IMAGE':data['gitBuilderImage'],
                'GIT_VERSION':data['tools']['git']['version'], 'GIT_SHA256':data['tools']['git']['sha256']}}
            prefix='./features/' if default else '../features/'
            features=cfg['features']
            features['./features/node'].update(data['tools']['node'])
            features['./features/gilt']['version']=data['tools']['gilt']
            features['./features/cli-tools'].update(data['tools']['cliTools'])
            features['ghcr.io/dhoeric/features/k9s:1']['version']=data['tools']['k9s']
            features['ghcr.io/devcontainers/features/kubectl-helm-minikube:1'].update(data['tools']['kubernetes'])
            cfg['features']={k.replace('./features/',prefix):v for k,v in features.items()}
            cfg['overrideFeatureInstallOrder']=[s.replace('./features/',prefix) for s in cfg['overrideFeatureInstallOrder']]
            cfg['containerEnv']={'ANSIBLE_MAJOR':major,'MOLECULE_TARGET_IMAGE':variant['pythonImage']}
            path=ROOT/'.devcontainer/devcontainer.json' if default else ROOT/f'.devcontainer/ansible{major}/devcontainer.json'
            result[path]=json.dumps(cfg,indent=2,ensure_ascii=False)+'\n'
    replacements={'CHECKOUT':data['actions']['actions/checkout'], 'SETUP_NODE':data['actions']['actions/setup-node'],
                  'UPLOAD':data['actions']['actions/upload-artifact'], 'BUILDX':data['actions']['docker/setup-buildx-action'],
                  'NODE':data['tools']['node']['version'], 'DEVCONTAINER':data['devcontainerCli']}
    for feature,values in [('node',data['tools']['node']),('cli-tools',data['tools']['cliTools']),('gilt',{'version':data['tools']['gilt']})]:
        path=ROOT/f'.devcontainer/features/{feature}/devcontainer-feature.json'
        metadata=read_json(path)
        for key,value in values.items():metadata['options'][key]['default']=value
        result[path]=json.dumps(metadata,indent=2,ensure_ascii=False)+'\n'
    dockerfile=ROOT/'.devcontainer/Dockerfile'
    text=dockerfile.read_text()
    defaults={'PYTHON_IMAGE':data['variants'][data['default']]['pythonImage'], 'GIT_BUILDER_IMAGE':data['gitBuilderImage'],
              'GIT_VERSION':data['tools']['git']['version'],'GIT_SHA256':data['tools']['git']['sha256'],
              'ANSIBLE_MAJOR':data['default'],'REQUIREMENTS_FILE':'requirements/ansible'+data['default']+'.txt'}
    for key,value in defaults.items():text=re.sub(r'^ARG '+key+r'=.*$', 'ARG '+key+'='+value,text,flags=re.M)
    result[dockerfile]=text
    for template_path in (ROOT/'.github/workflow-templates').glob('*.yml'):
        text=template_path.read_text()
        for key,value in replacements.items():text=text.replace('@'+key+'@',value)
        result[ROOT/'.github/workflows'/template_path.name]=text
    readme=ROOT/'README.md'
    if readme.exists() and (ROOT/'compatibility/resolved.json').exists():
        text=readme.read_text()
        selected=read_json(ROOT/'compatibility/resolved.json')['packages']
        table=['| Образ | Ansible | ansible-core | Python контроллера | Python целевых узлов (upstream) | Molecule | ansible-lint / ansible-compat |',
               '|---|---|---|---|---|---|---|']
        for major,variant in data['variants'].items():
            p=selected[major];py=variant['pythonImage'].split(':',1)[1].split('-')[0]
            targets=variant['targetPython']
            table.append(f'| {major} | {p["ansible"]} | {p["ansible-core"]} | {py} | {targets[0]}–{targets[-1]} | {p["molecule"]} | {p["ansible-lint"]} / {p["ansible-compat"]} |')
        text=re.sub(r'<!-- compatibility:start -->.*?<!-- compatibility:end -->','<!-- compatibility:start -->\n'+'\n'.join(table)+'\n<!-- compatibility:end -->',text,flags=re.S)
        tools=data['tools']
        rows={'Node.js':tools['node']['version'],'npm':tools['node']['npmVersion'],'Git':tools['git']['version'],
              'Claude Code':tools['cliTools']['claudeVersion'],'elasticdump':tools['cliTools']['elasticdumpVersion'],
              'kubectl':tools['kubernetes']['version'],'Helm':tools['kubernetes']['helm'],'minikube':tools['kubernetes']['minikube'],
              'k9s':tools['k9s'],'Gilt':tools['gilt'],'devcontainer CLI (host/CI)':data['devcontainerCli']}
        tool_table='| Инструмент | Версия |\n|---|---|\n'+'\n'.join(f'| {name} | {value} |' for name,value in rows.items())
        text=re.sub(r'<!-- tools:start -->.*?<!-- tools:end -->','<!-- tools:start -->\n'+tool_table+'\n<!-- tools:end -->',text,flags=re.S)
        sizes=['| Платформа | Образ | Несжатый размер | Проверено | Состояние lock |','|---|---|---|---|---|']
        validation=ROOT/'compatibility/validation.json'
        if validation.exists():
            for arch,report in read_json(validation).items():
                for major,row in report['images'].items():
                    current=hashlib.sha256((ROOT/f'requirements/ansible{major}.txt').read_bytes()).hexdigest()==row['lockSha256'] and row['pythonImage']==data['variants'][major]['pythonImage'] and row.get('manifestSha256')==hashlib.sha256((ROOT/'images.json').read_bytes()).hexdigest()
                    sizes.append(f'| {arch} | {major} | {row["bytes"]:,} байт | {report["date"][:10]} | '+('текущий' if current else 'предыдущее окружение')+' |')
        else:sizes=['Полный прогон ещё не записан. Выполните `make test` и `make record`.']
        text=re.sub(r'<!-- sizes:start -->.*?<!-- sizes:end -->','<!-- sizes:start -->\n'+'\n'.join(sizes)+'\n<!-- sizes:end -->',text,flags=re.S)
        result[readme]=text
    return result

def render(check=False):
    stale=[]
    for path,text in generated().items():
        if not path.exists() or path.read_text()!=text:
            stale.append(str(path.relative_to(ROOT)))
            if not check:
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(text)
    if check and stale:
        raise SystemExit('Generated configuration is stale: '+', '.join(stale))
    return stale

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true')
    render(parser.parse_args().check)
