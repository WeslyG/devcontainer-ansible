import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import publish
import render

class PublicationTests(unittest.TestCase):
    def fixture(self,root):
        (root/'requirements').mkdir()
        data={'variants':{major:{'maxImageBytes':1000,'pythonImage':'python:'+major} for major in publish.VARIANTS}}
        (root/'images.json').write_text(json.dumps(data))
        for major in publish.VARIANTS:(root/f'requirements/ansible{major}.txt').write_text('pin-'+major)
        release='2026.01.04-2';revision='a'*40;directory=root/'downloaded'
        for major in publish.VARIANTS:
            for index,arch in enumerate(publish.ARCHES):
                row={'tested':True,'variant':major,'arch':arch,'platform':'linux/'+arch,
                     'platformVersion':release,'revision':revision,'repository':publish.REPOSITORY,
                     'image':f'ansible-infra:ansible{major}-{release}',
                     'nativeTag':publish.native_tag(major,arch,release),'pythonImage':'python:'+major,
                     'manifestSha256':publish.sha(root/'images.json'),
                     'lockSha256':publish.sha(root/f'requirements/ansible{major}.txt'),
                     'digest':'sha256:'+str(index+1)*64,'imageConfigDigest':'sha256:'+'d'*64,'imageId':'sha256:'+'c'*64,'bytes':500}
                folder=directory/f'validation-ansible{major}-{release}-{arch}'
                folder.mkdir(parents=True);(folder/f'publish-{major}-{arch}.json').write_text(json.dumps(row))
                measured=root/f'.build/{arch}/results.json';measured.parent.mkdir(parents=True,exist_ok=True)
                contents=json.loads(measured.read_text()) if measured.exists() else {'images':{}}
                contents['images'][major]=row;measured.write_text(json.dumps(contents))
        return directory,release,revision

    def test_complete_native_matrix_and_expected_tags(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);directory,release,revision=self.fixture(root)
            plan=publish.publication_plan(directory,release,revision,root)
            self.assertEqual(set(plan),{'10','12','14'})
            self.assertEqual(publish.release_tag('10',release),'weslyg/ansible-infra:ansible10-2026.01.04-2')
            self.assertEqual(publish.native_tag('10','arm64',release),'weslyg/ansible-infra:arm64-ansible10-2026.01.04-2')
            self.assertTrue(publish.checked_result('10','amd64',release,root)['tested'])

    def test_publication_rejects_untested_stale_mismatched_and_oversized_images(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);directory,release,revision=self.fixture(root)
            path=directory/f'validation-ansible10-{release}-amd64/publish-10-amd64.json'
            original=json.loads(path.read_text())
            for field,value in [('tested',False),('platform','linux/arm64'),('revision','b'*40),
                                ('platformVersion','2026.01.05'),('manifestSha256','bad'),
                                ('lockSha256','bad'),('digest','not-a-digest'),('imageId',''),
                                ('repository','other/repo'),('bytes',1001),('nativeTag','wrong')]:
                with self.subTest(field=field):
                    row={**original,field:value};path.write_text(json.dumps(row))
                    with self.assertRaises(ValueError):publish.publication_plan(directory,release,revision,root)
            path.write_text(json.dumps(original));path.unlink()
            with self.assertRaises(FileNotFoundError):publish.publication_plan(directory,release,revision,root)

    def test_local_result_requires_exact_lock_and_successful_tests(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);_,release,_=self.fixture(root)
            path=root/'.build/amd64/results.json';report=json.loads(path.read_text())
            report['images']['10']['tested']=False;path.write_text(json.dumps(report))
            with self.assertRaises(ValueError):publish.checked_result('10','amd64',release,root)

    def test_registry_content_matches_both_image_store_id_schemes(self):
        local={'Id':'sha256:'+'a'*64,'Os':'linux','Architecture':'amd64',
               'RootFS':{'Layers':['sha256:'+'b'*64]},
               'Config':{'Env':['A=1'],'User':'','Labels':{'empty':''},
                         'Shell':['/bin/sh','-c'],'Healthcheck':{'Test':['CMD','/bin/true']}}}
        remote=copy.deepcopy(local);remote['Config'].pop('User')
        self.assertTrue(publish.matches_image_config(remote,local))
        local['Id']='sha256:'+'c'*64
        self.assertTrue(publish.matches_image_config(remote,local))
        changed=copy.deepcopy(remote);changed['RootFS']['Layers']=['sha256:'+'d'*64]
        self.assertFalse(publish.matches_image_config(changed,local))
        changed=copy.deepcopy(remote);changed['Config']['Env']=['A=2']
        self.assertFalse(publish.matches_image_config(changed,local))
        changed=copy.deepcopy(remote);changed['Config']['Labels']={}
        self.assertFalse(publish.matches_image_config(changed,local))
        for field in ['Shell','Healthcheck']:
            changed=copy.deepcopy(remote);changed['Config'].pop(field)
            self.assertFalse(publish.matches_image_config(changed,local))

    def test_manifest_requires_exact_two_platforms_and_digests(self):
        digests={'amd64':'sha256:'+'1'*64,'arm64':'sha256:'+'2'*64}
        document={'manifests':[{'platform':{'os':'linux','architecture':arch},'digest':digest} for arch,digest in digests.items()]}
        self.assertTrue(publish.matches_manifest(document,digests))
        missing=copy.deepcopy(document);missing['manifests'].pop()
        self.assertFalse(publish.matches_manifest(missing,digests))
        wrong=copy.deepcopy(document);wrong['manifests'][0]['digest']='sha256:'+'3'*64
        self.assertFalse(publish.matches_manifest(wrong,digests))
        self.assertFalse(publish.matches_manifest({'manifests':document['manifests']*2},digests))

    def test_workflow_guards_publication_and_waits_for_matrix(self):
        workflows={p.name:text for p,text in render.generated().items() if p.parent.name=='workflows'}
        text=workflows['build.yml']
        guard="if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'"
        self.assertGreaterEqual(text.count(guard),4)
        self.assertIn('needs: [version, image]',text)
        self.assertIn('cancel-in-progress: false',text)
        self.assertLess(text.index('scripts/build.py'),text.index('scripts/publish.py stage'))
        self.assertNotIn('scripts/publish.py',workflows['update.yml'])
