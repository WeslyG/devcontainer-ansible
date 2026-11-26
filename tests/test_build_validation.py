import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build import runtime_configuration

class RuntimeConfigurationTests(unittest.TestCase):
    def test_frozen_image_keeps_runtime_settings_and_controller_uid(self):
        source={'build':{'dockerfile':'Dockerfile'},'features':{'./feature':{}},
                'overrideFeatureInstallOrder':['./feature'],'updateRemoteUserUID':True,
                'remoteUser':'vscode','runArgs':['--net=host'],
                'mounts':['type=bind,source=/a,target=/b'],
                'containerEnv':{'ANSIBLE_MAJOR':'12'},'postCreateCommand':'echo ready'}
        original=copy.deepcopy(source)
        image_id='sha256:'+'a'*64
        actual=runtime_configuration(source,image_id)
        self.assertEqual(actual['image'],image_id)
        self.assertFalse(actual['updateRemoteUserUID'])
        self.assertTrue({'build','features','overrideFeatureInstallOrder'}.isdisjoint(actual))
        for key in ['remoteUser','runArgs','mounts','containerEnv','postCreateCommand']:
            self.assertEqual(actual[key],source[key])
        self.assertEqual(source,original)

    def test_mutable_tag_cannot_select_validation_artifact(self):
        with self.assertRaises(ValueError):
            runtime_configuration({'image':'example:old'},'example:latest')

if __name__=='__main__':unittest.main()
