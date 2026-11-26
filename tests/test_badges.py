import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from badges import collect,markdown,replace_block,START,END

class SecurityBadgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.args=('2026.11.27','a'*40,'123','WeslyG/devcontainer-ansible')
    def add(self,arch='amd64',attempt=1,count=96,status='findings'):
        folder=self.root/f'{arch}-{attempt}';folder.mkdir()
        data={'release':self.args[0],'revision':self.args[1],'runId':self.args[2],
              'arch':arch,'runAttempt':str(attempt),'images':{v:{'digest':'sha256:'+'b'*64,
              'status':status,'highCritical':count,'accepted':2 if v=='10' else 0} for v in ('10','12','14')}}
        (folder/'scan-metadata.json').write_text(json.dumps(data));return folder/'scan-metadata.json'
    def test_current_findings_and_missing_architecture_are_not_green(self):
        self.add();snapshot=collect(self.root,*self.args);text=markdown(snapshot)
        self.assertEqual(text.count('96%20High%2FCritical-red'),3)
        self.assertEqual(text.count('scan%20error-lightgrey'),3)
        self.assertNotIn('brightgreen',text)
    def test_zero_completed_scans_are_green_and_preserve_run_link(self):
        self.add(count=0,status='pass');self.add('arm64',count=0,status='pass')
        text=markdown(collect(self.root,*self.args))
        self.assertEqual(text.count('0%20High%2FCritical-brightgreen'),6)
        self.assertIn('/actions/runs/123#artifacts',text)
    def test_latest_attempt_error_replaces_old_success_without_zero(self):
        self.add(count=0,status='pass');self.add(attempt=2,count=None,status='error')
        snapshot=collect(self.root,*self.args)
        self.assertIsNone(snapshot['architectures']['amd64']['images']['10']['highCritical'])
        self.assertNotIn('brightgreen',markdown(snapshot))
    def test_mixed_release_or_run_is_rejected(self):
        p=self.add();data=json.loads(p.read_text());data['runId']='999';p.write_text(json.dumps(data))
        with self.assertRaises(ValueError):collect(self.root,*self.args)
    def test_invalid_pass_count_and_symlink_are_rejected(self):
        p=self.add(count=96,status='pass')
        with self.assertRaises(ValueError):collect(self.root,*self.args)
        p.unlink();(self.root/'outside.json').write_text('{}');p.symlink_to(self.root/'outside.json')
        with self.assertRaises(ValueError):collect(self.root,*self.args)
    def test_marker_replacement_preserves_other_content(self):
        self.add();snapshot=collect(self.root,*self.args)
        text=replace_block('intro\n'+START+'\nold\n'+END+'\noutro',snapshot)
        self.assertTrue(text.startswith('intro\n'));self.assertTrue(text.endswith('\noutro'))
        self.assertNotIn('\nold\n',text)
        with self.assertRaises(ValueError):replace_block('no markers',snapshot)

    def test_status_only_new_attempt_is_grey_instead_of_previous_green(self):
        self.add(count=0,status='pass')
        folder=self.root/'security-2026.11.27-amd64-attempt2';folder.mkdir()
        (folder/'status.json').write_text('{"kind":"scan","files":[]}')
        snapshot=collect(self.root,*self.args)
        self.assertEqual(snapshot['architectures']['amd64']['runAttempt'],'2')
        self.assertIsNone(snapshot['architectures']['amd64']['images']['10']['highCritical'])
        self.assertNotIn('brightgreen',markdown(snapshot))

    def test_no_metadata_produces_six_unknown_counts(self):
        snapshot=collect(self.root,*self.args)
        self.assertEqual(markdown(snapshot).count('scan%20error-lightgrey'),6)
        self.assertNotIn('brightgreen',markdown(snapshot))

    def test_old_release_run_and_attempt_cannot_roll_back_snapshot(self):
        from badges import keep_newer
        self.add(count=0,status='pass');candidate=collect(self.root,*self.args)
        current=copy.deepcopy(candidate);current['release']='2026.11.28'
        self.assertEqual(keep_newer(candidate,current),current)
        current=copy.deepcopy(candidate);current['runId']='200'
        self.assertEqual(keep_newer(candidate,current),current)
        newer=copy.deepcopy(candidate);newer['release']='2026.11.27-10'
        older=copy.deepcopy(candidate);older['release']='2026.11.27-2'
        self.assertEqual(keep_newer(newer,older),newer)
        current=copy.deepcopy(candidate)
        current['architectures']['amd64']['runAttempt']='2'
        current['architectures']['amd64']['images']['10'].update(status='error',highCritical=None)
        self.assertIsNone(keep_newer(candidate,current)['architectures']['amd64']['images']['10']['highCritical'])

if __name__=='__main__':unittest.main()
