"""Export only explicitly named public dependency/validation files, never a directory tree."""
import argparse
import shutil
from common import ROOT, write_json

def export(kind,arch='amd64',root=ROOT):
    out=root/'artifacts';out.mkdir(exist_ok=True)
    files=([root/f'.build/{arch}/results.json',root/'images.json'] if kind=='build' else
           [root/'.build/update.patch',root/'.build/latest-releases.json',root/'compatibility/packages.json',root/'compatibility/resolved.json'])
    copied=[]
    for source in files:
        if source.is_file():
            if source.is_symlink() or not source.resolve().is_relative_to(root.resolve()):
                raise ValueError('Refusing an artifact source outside the repository')
            shutil.copyfile(source,out/source.name);copied.append(source.name)
    write_json(out/'status.json',{'kind':kind,'files':copied})
    return copied

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['build','update']);parser.add_argument('--arch',choices=['amd64','arm64'],default='amd64');args=parser.parse_args()
    export(args.kind,args.arch)
