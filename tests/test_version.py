import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import version
from common import image

class ReleaseTests(unittest.TestCase):
    def test_date_and_increment_across_variants(self):
        day='2026.01.04'
        self.assertEqual(version.choose(day,[]),day)
        self.assertEqual(version.choose(day,['ansible10-'+day]),day+'-1')
        self.assertEqual(version.choose(day,['ansible12-'+day+'-2','ansible14-'+day+'-9','ansible10-2026.01.03-99','ansible10-'+day+'-1-arm64']),day+'-10')
    def test_strict_version_and_calendar(self):
        for value in ['2026.1.04','2026.01.4','2026.02.30','2026.01.04-0','2026.01.04-01','2026.01.04-1-2','2026.01.04\nINJECT=x']:
            with self.assertRaises(ValueError):version.validate(value)
        self.assertEqual(version.validate('2026.01.04-12'),'2026.01.04-12')
    def test_registry_pagination_and_errors(self):
        page='https://hub.docker.com/v2/repositories/weslyg/ansible-infra/tags?page=2'
        with patch.object(version,'fetch',side_effect=[{'results':[{'name':'a'}],'next':page},{'results':[{'name':'b'}],'next':None},{'results':[],'next':None},{'results':[],'next':None}]) as fetch:
            self.assertEqual(version.registry_tags('2026.01.04'),['a','b'])
            self.assertEqual(fetch.call_count,4)
        with patch.object(version,'fetch',side_effect=RuntimeError('offline')):
            with self.assertRaises(RuntimeError):version.registry_tags('2026.01.04')
    def test_image_tag_keeps_date_separate_from_suffix(self):
        with patch.dict(os.environ,{'PLATFORM_VERSION':'2026.01.04-2'}):
            self.assertEqual(image('10'),'ansible-infra:ansible10-2026.01.04-2')
