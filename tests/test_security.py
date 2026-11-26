import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import security

def finding(package='liblmdb0',cve='CVE-2019-16224',severity='CRITICAL'):
    return {'PkgName':package,'VulnerabilityID':cve,'Severity':severity,'InstalledVersion':{'ansible':'10.7.0','ansible-core':'2.17.14'}.get(package,'1.0')}

class SecurityTests(unittest.TestCase):
    def report(self,*items):
        return {'SchemaVersion':2,'Results':[{'Target':'Debian','Type':'debian','Vulnerabilities':[]},{'Target':'Python','Type':'python-pkg','Vulnerabilities':list(items)}]}

    def test_ansible10_exception_is_limited_to_package_and_variant(self):
        item=finding('ansible-core','CVE-2026-11332','HIGH')
        self.assertEqual(security.evaluate(self.report(item),'10')['blocked'],[])
        self.assertEqual(len(security.evaluate(self.report(item),'12')['blocked']),1)
        self.assertEqual(len(security.evaluate(self.report(finding()),'10')['blocked']),1)

    def test_unknown_ansible_cve_requires_review(self):
        self.assertEqual(len(security.evaluate(self.report(finding('ansible-core','CVE-2099-1234')),'10')['blocked']),1)

    def test_unfixed_critical_and_fixed_high_both_block(self):
        a=finding();b=finding('glob','CVE-2026-118773','HIGH');b['FixedVersion']='14.0.2'
        self.assertEqual(len(security.evaluate(self.report(a,b),'10')['blocked']),2)

    def test_all_findings_are_retained_including_accepted_and_medium(self):
        result=security.evaluate(self.report(finding('ansible','CVE-2025-14010','MEDIUM'),finding(severity='LOW')),'10')
        self.assertEqual(len(result['findings']),2)
        self.assertEqual(len(result['accepted']),1)
        self.assertEqual(result['blocked'],[])

    def test_language_only_report_cannot_claim_full_image_scan(self):
        with self.assertRaises(ValueError):
            security.evaluate({'SchemaVersion':2,'Results':[{'Target':'Python','Type':'python-pkg'}]},'10')

    def test_exception_does_not_accept_another_core_family(self):
        item=finding('ansible-core','CVE-2026-11332','HIGH');item['InstalledVersion']='2.19.0'
        self.assertEqual(len(security.evaluate(self.report(item),'10')['blocked']),1)

    def test_missing_results_is_not_a_clean_scan(self):
        with self.assertRaises(ValueError):security.evaluate({},'10')

if __name__=='__main__':unittest.main()
