import copy
import sys
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import render
import artifacts
from common import jsonc

class ConfigurationTests(unittest.TestCase):
    def test_artifact_export_ignores_unlisted_and_hidden_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'.build/amd64').mkdir(parents=True)
            (root/'.build/amd64/results.json').write_text('{}')
            (root/'.build/amd64/.secret').write_text('must stay local')
            (root/'.build/credentials.json').write_text('must stay local')
            (root/'images.json').write_text('{}')
            copied=artifacts.export('build',root=root)
            self.assertEqual(set(copied),{'results.json','images.json'})
            self.assertEqual({p.name for p in (root/'artifacts').iterdir()},{'results.json','images.json','status.json'})

    def test_jsonc_keeps_urls_and_literal_comment_markers(self):
        self.assertEqual(jsonc('{"url":"https://example.org/a//b",/* comment */"text":"/* literal */"//comment\n}'),{'url':'https://example.org/a//b','text':'/* literal */'})

    def test_variant_paths_and_node_before_npm_consumer(self):
        for path,text in render.generated().items():
            if path.name!='devcontainer.json':continue
            import json
            cfg=json.loads(text)
            base=path.parent
            self.assertTrue((base/cfg['build']['dockerfile']).resolve().is_file())
            self.assertTrue((base/cfg['build']['context']).resolve().is_dir())
            local=[k for k in cfg['features'] if k.startswith('.')]
            for feature in local:self.assertTrue((base/feature/'install.sh').resolve().is_file())
            order=cfg['overrideFeatureInstallOrder']
            node=next(k for k in local if k.endswith('/node'))
            tools=next(k for k in local if k.endswith('/cli-tools'))
            self.assertLess(order.index(node),order.index(tools))

    def test_all_variants_keep_controller_family(self):
        import json
        for path,text in render.generated().items():
            if path.name!='devcontainer.json':continue
            cfg=json.loads(text);major=cfg['containerEnv']['ANSIBLE_MAJOR']
            self.assertEqual(cfg['build']['args']['ANSIBLE_MAJOR'],major)
            self.assertEqual(cfg['build']['args']['REQUIREMENTS_FILE'],f'requirements/ansible{major}.txt')

if __name__=='__main__':unittest.main()
