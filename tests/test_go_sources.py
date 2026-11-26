import copy
import sys
from pathlib import Path
import unittest
import subprocess
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import go_sources
from common import matrix

class SourcePinsTests(unittest.TestCase):
    def test_canonical_cli_version_cannot_drift_from_source_pin(self):
        data=copy.deepcopy(matrix());data['tools']['k9s']='0.99.0'
        with self.assertRaises(ValueError):go_sources.configuration(data)

    def test_containerd_uses_latest_patch_with_compatible_kubernetes_api(self):
        versions=['v2.4.2','v2.3.7','v2.2.9','v2.2.10','v2.2.11']
        modules={'v2.4.2':'k8s.io/client-go v0.37.0','v2.3.7':'k8s.io/client-go v0.36.0','v2.2.11':'k8s.io/client-go v0.35.0'}
        self.assertEqual(go_sources.compatible_containerd(versions,'v0.35.1',modules.__getitem__),'v2.2.11')
        self.assertEqual(go_sources.compatible_containerd(versions,'v0.37.3',modules.__getitem__),'v2.4.2')

    def test_source_inventory_keeps_real_module_versions(self):
        rows=go_sources.sbom(matrix())['components']
        self.assertEqual(len(rows),5)
        self.assertTrue(all(row['version'] not in ('devel','(devel)','v0.0.0') for row in rows))
        self.assertTrue(all(row['version'] in row['purl'] for row in rows))

    def make_version(self,text,key='ISO_VERSION'):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'Makefile';path.write_text(text)
            script=Path(__file__).resolve().parents[1]/'.devcontainer/features/gilt/build-extras.sh'
            return subprocess.run(['bash','-c','source "$1"; make_literal_version "$2" "$3"','_',str(script),key,str(path)],capture_output=True,text=True)

    def test_minikube_versions_are_literals_in_makefile_without_iso_file(self):
        text='ISO_VERSION ?= v1.39.0\nSTORAGE_PROVISIONER_TAG ?= v5\n'
        result=self.make_version(text)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'v1.39.0')
        self.assertEqual(self.make_version(text,'STORAGE_PROVISIONER_TAG').stdout.strip(),'v5')

    def test_minikube_makefile_expressions_are_rejected_without_evaluation(self):
        result=self.make_version('ISO_VERSION ?= $(shell echo unsafe)\n')
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn('unsafe',result.stdout)

    def test_minikube_literal_followed_by_expression_requires_review(self):
        for expression in ('$(OTHER_VERSION)','$(shell echo v1.40.0)'):
            text='ISO_VERSION ?= v1.39.0\nISO_VERSION := '+expression+'\n'
            self.assertNotEqual(self.make_version(text).returncode,0)

    def test_minikube_append_or_shell_assignment_requires_review(self):
        for operator in ('+=','!='):
            self.assertNotEqual(self.make_version('ISO_VERSION '+operator+' v1.39.0\n').returncode,0)

    def test_minikube_missing_or_ambiguous_versions_require_review(self):
        for text in ('# no version\n','ISO_VERSION ?= v1.39.0\nISO_VERSION := v1.40.0\n'):
            self.assertNotEqual(self.make_version(text).returncode,0)

if __name__=='__main__':unittest.main()
