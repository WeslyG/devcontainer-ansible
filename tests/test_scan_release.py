import sys
from pathlib import Path
import tempfile
import tarfile
import unittest
import json
import subprocess
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import scan_release
from scan_release import archive_reports, summary

class PublishedScanTests(unittest.TestCase):
    def test_archive_only_explicit_public_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/'trivy-10.json').write_text('{}')
            (folder/'secret').write_text('do not export')
            result=archive_reports(folder,'amd64')
            with tarfile.open(result) as archive:
                self.assertEqual(archive.getnames(),['trivy-10.json'])

    def test_archive_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/'secret').write_text('private')
            (folder/'trivy-10.json').symlink_to(folder/'secret')
            with self.assertRaises(ValueError):archive_reports(folder,'amd64')

    def test_summary_distinguishes_scanner_failure_and_findings(self):
        text=summary({'release':'2026.11.26','arch':'amd64','images':{
            '10':{'digest':'sha256:abc','highCritical':5,'accepted':1,'status':'findings'},
            '12':{'digest':'sha256:def','status':'error','error':'scanner failed'}}})
        self.assertIn('findings',text)
        self.assertIn('error',text)
        self.assertIn('sha256:abc',text)

    def test_failure_in_one_variant_keeps_other_snapshots_and_fails_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'scripts').mkdir()
            (root/'scripts/security.py').write_text('policy')
            db=root/'.build/trivy-cache/db';db.mkdir(parents=True)
            (db/'trivy.db').write_bytes(b'database snapshot')
            (db/'metadata.json').write_text('{}')
            folder=root/'.build/published-scan/amd64'
            clean={'SchemaVersion':2,'Results':[{'Target':'Debian','Type':'debian','Vulnerabilities':[]}]}
            calls=[]
            def run(command,**kwargs):
                calls.append(command)
                if command[:3]==['docker','image','inspect']:return subprocess.CompletedProcess(command,1)
                if '--output' in command and 'image' in command:
                    name=Path(command[command.index('--output')+1]).name
                    if name=='trivy-12.json':raise subprocess.CalledProcessError(2,command)
                    (folder/name).write_text(json.dumps(clean))
                if 'convert' in command:
                    name=Path(command[command.index('--output')+1]).name
                    (folder/name).write_text('{}')
                return subprocess.CompletedProcess(command,0)
            plan={major:{'amd64':'sha256:'+major*32} for major in ('10','12','14')}
            with patch.object(scan_release,'ROOT',root), patch.object(scan_release,'publication_plan',return_value=plan), \
                 patch.object(scan_release,'matrix',return_value={'security':{'trivyImage':'scanner@sha256:fixed'}}), \
                 patch.object(scan_release.subprocess,'run',side_effect=run), \
                 patch.object(scan_release.subprocess,'check_output',return_value='revision'), \
                 patch.dict('os.environ',{'PLATFORM_VERSION':'2026.11.26'},clear=True), \
                 patch.object(sys,'argv',['scan_release.py','--directory',str(root),'--arch','amd64']):
                with self.assertRaises(SystemExit) as raised:scan_release.main()
            self.assertEqual(raised.exception.code,1)
            metadata=json.loads((folder/'scan-metadata.json').read_text())
            self.assertEqual([row['status'] for row in metadata['images'].values()],['pass','error','pass'])
            self.assertTrue((folder/'trivy-14.json').exists())
            self.assertEqual(len([cmd for cmd in calls if cmd[:2]==['docker','pull']]),3)
            self.assertTrue(all('@sha256:' in cmd[-1] for cmd in calls if cmd[:2]==['docker','pull']))
            self.assertFalse(any('push' in cmd for cmd in calls))

    def test_database_failure_still_records_all_requested_image_identities(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'scripts').mkdir();(root/'scripts/security.py').write_text('policy')
            plan={major:{'amd64':'sha256:'+major*32} for major in ('10','12','14')}
            with patch.object(scan_release,'ROOT',root), patch.object(scan_release,'publication_plan',return_value=plan), \
                 patch.object(scan_release,'matrix',return_value={'security':{'trivyImage':'scanner@sha256:fixed'}}), \
                 patch.object(scan_release.subprocess,'run',side_effect=subprocess.CalledProcessError(2,['scanner'])), \
                 patch.object(scan_release.subprocess,'check_output',return_value='revision'), \
                 patch.dict('os.environ',{'PLATFORM_VERSION':'2026.11.26'},clear=True), \
                 patch.object(sys,'argv',['scan_release.py','--directory',str(root),'--arch','amd64']):
                with self.assertRaises(SystemExit):scan_release.main()
            metadata=json.loads((root/'.build/published-scan/amd64/scan-metadata.json').read_text())
            self.assertEqual(set(metadata['images']),{'10','12','14'})
            self.assertTrue(all(row['status']=='not_scanned' for row in metadata['images'].values()))
            self.assertIn('error',metadata)

if __name__=='__main__':unittest.main()
