""" Tests for policy.py """
import unittest

import datetime
import json
import mock
import dateutil.tz

from starttls_policy_cli import policy
from starttls_policy_cli import util
from starttls_policy_cli.tests.util import assertRaisesRegex, param, parametrize_over

test_json = '{\
    "author": "Electronic Frontier Foundation",\
        "expires": "2014-05-26T01:35:33+0000",\
        "timestamp": "2014-05-26T01:35:33+0000",\
        "policies": {\
            ".valid.example-recipient.com": {\
                "min-tls-version": "TLSv1.1",\
                    "mode": "enforce",\
                    "mxs": [".valid.example-recipient.com"],\
                    "tls-report": "https://tls-rpt.example-recipient.org/api/report"\
            }\
        }\
    }'

class TestConfigEncoder(unittest.TestCase):
    """Tests extensions to JSON serializer for dumping configs"""

    def encode_test(self, obj, expected):
        """Parametrized test for JSON encoder"""
        self.assertEqual(json.dumps(obj, sort_keys=True, cls=policy.ConfigEncoder), expected)

parametrize_over(TestConfigEncoder, TestConfigEncoder.encode_test,
                 [
                    param("encode_none", None, "null"),
                    param("encode_empty_list", [], "[]"),
                    param("encode_empty_dict", {}, "{}"),
                    param("encode_empty_string", "", '""'),
                    param("encode_integer", 0, "0"),
                    param("encode_true", True, "true"),
                    param("encode_false", False, "false"),
                    param("encode_float", .1, "0.1"),
                    param("encode_datetime",
                          datetime.datetime.fromtimestamp(0, tz=dateutil.tz.tzutc()),
                          '"1970-01-01T00:00:00+0000"'),
                 ])

class TestConfig(unittest.TestCase):
    # pylint: disable=too-many-public-methods
    """Testing configuration
    """

    maxDiff = None

    def setUp(self):
        self.conf = policy.Config()
        self.conf.author = "EFF"
        self.conf.expires = datetime.datetime.now()
        self.conf.timestamp = datetime.datetime.now()
        self.sample_policy = {
            'mxs': ['eff.org', '.eff.org'],
            'mode': 'testing'
        }
        self.other_policy = {
            'mxs': ['example.com', '.example.com'],
            'mode': 'enforce'
        }
        self.conf.policies = {'eff.org': self.sample_policy}

    def test_flush(self):
        with mock.patch("starttls_policy_cli.policy.open", mock.mock_open()) as m:
            self.conf.flush("lol.txt")
            m.assert_called_with("lol.txt", "w")
            m().write.assert_called_once()

    def test_flush_default(self):
        with mock.patch("starttls_policy_cli.policy.open", mock.mock_open()) as m:
            self.conf.flush()
            m.assert_called_with(self.conf.filename, "w")
            m().write.assert_called_once()

    def test_merge_keeps_old_settings(self):
        conf2 = policy.Config()
        conf2.author = "EFF"
        updated_timestamp = self.conf.expires - datetime.timedelta(days=1)
        conf2.timestamp = updated_timestamp
        new_conf = self.conf.merge(conf2)
        self.assertEqual(new_conf.author, "EFF")
        self.assertTrue(new_conf.timestamp is not None)
        self.assertEqual(new_conf.timestamp, updated_timestamp)

    def test_update_drops_old_settings(self):
        conf2 = policy.Config()
        conf2.author = "EFF"
        new_conf = self.conf.update(conf2)
        self.assertEqual(new_conf.author, "EFF")
        self.assertEqual(new_conf.timestamp, None)

    def test_merge_keeps_old_policies(self):
        conf2 = policy.Config()
        conf2.policies = {'example.com': self.other_policy}
        new_conf = self.conf.merge(conf2)
        self.assertTrue('example.com' in new_conf.policies)
        self.assertTrue('eff.org' in new_conf.policies)

    def test_update_drops_old_policies(self):
        conf2 = policy.Config()
        conf2.policies = {'example.com': self.other_policy}
        new_conf = self.conf.update(conf2)
        self.assertTrue('example.com' in new_conf.policies)
        self.assertFalse('eff.org' in new_conf.policies)

    def test_should_update_invalid_type(self):
        self.assertFalse(self.conf.should_update(None))

    def test_should_update_valid_type(self):
        conf2 = policy.Config()
        conf2.policies = {'example.com': self.other_policy}
        self.assertTrue(self.conf.should_update(conf2))

    def test_updateble_checks_types(self):
        with assertRaisesRegex(self, util.ConfigError,
                                     "Attempting to update a "
                                     "<class 'starttls_policy_cli.policy.Config'> "
                                     "with a <(type|class) 'NoneType'>"):
            self.conf.update(None)

    def test_len_method(self):
        conf2 = policy.Config()
        conf2.policies = {'example.com': self.other_policy}
        self.assertEqual(len(conf2), 1)

    def test_keys_empty_policy(self):
        conf2 = policy.Config()
        with self.assertRaises(StopIteration):
            next(iter(conf2.keys()))

    def test_basic_parsing(self):
        obj = json.loads(test_json)
        self.conf.load_from_dict(obj)
        self.assertEqual(self.conf.author, "Electronic Frontier Foundation")
        self.assertEqual(json.loads(self.conf.dump()), obj)

    def test_timestamp_and_expires_required(self):
        with self.assertRaises(util.ConfigError):
            policy.Config().load_from_dict({'expires': datetime.datetime.now()})
        with self.assertRaises(util.ConfigError):
            policy.Config().load_from_dict({'timestamp': datetime.datetime.now()})
        conf = policy.Config()
        conf.load_from_dict({'timestamp': datetime.datetime.now(),
                             'expires': datetime.datetime.now()})
        self.assertTrue(isinstance(conf.timestamp, datetime.datetime))
        self.assertTrue(isinstance(conf.expires, datetime.datetime))

    def test_set_author(self):
        with self.assertRaises(util.ConfigError):
            policy.Config().load_from_dict({'author': 0})
        with self.assertRaises(util.ConfigError):
            policy.Config().author = 0
        conf = policy.Config()
        conf.author = "me"
        self.assertEqual(conf.author, "me")

    def test_set_policies(self):
        invalid_policy = {'mode': 'none'}
        with self.assertRaises(util.ConfigError):
            policy.Config().policies = {'invalid': invalid_policy}
        conf = policy.Config()
        conf.policies = {'valid': {}}
        self.assertEqual(conf.get_policy_for('valid').min_tls_version, 'TLSv1.2')

    def test_set_aliased_policy(self):
        conf = policy.Config()
        conf.policy_aliases = {'valid': {}}
        with self.assertRaises(util.ConfigError):
            conf.policies = {'invalid': {'policy-alias': 'invalid'}}
        conf.policies = {'valid': {'policy-alias': 'valid'}}
        self.assertEqual(conf.get_policy_for('valid').min_tls_version, 'TLSv1.2')

    def test_set_pins_for_policy(self):
        conf = policy.Config()
        conf.pinsets = {'valid': 'lol a pin'}
        with self.assertRaises(util.ConfigError):
            conf.policies = {'invalid': {'pin': 'invalid'}}
        conf.policies = {'valid': {'pin': 'valid'}}
        self.assertEqual(conf.get_policy_for('valid').pin, 'valid')

    def test_iter_policies_aliased(self):
        conf = policy.Config()
        conf.policy_aliases = {'valid': {'tls-report': 'https://tls.report'}}
        conf.policies = {'valid1': {'policy-alias': 'valid'},
                         'valid2': {'policy-alias': 'valid'}}
        for val in conf:
            self.assertEqual(conf[val].tls_report, 'https://tls.report')

    def test_iter_policies(self):
        conf = policy.Config()
        sample_policy = {'tls-report': 'https://tls.report'}
        conf.policies = {'valid1': sample_policy,
                         'valid2': sample_policy}
        for val in conf:
            self.assertEqual(conf[val].tls_report, 'https://tls.report')

    def test_no_aliasing_in_alias(self):
        conf = policy.Config()
        with self.assertRaises(util.ConfigError):
            conf.policy_aliases = {'valid': {},
                                   'valid2': {'policy-alias': 'valid'}}

    def test_bad_schema(self):
        conf = policy.Config(schema={"author": "Author field here"})
        with self.assertRaises(util.ConfigError):
            conf.author = "Me"

class TestPolicy(unittest.TestCase):
    """Testing policy configuration
    """

    def setUp(self):
        self.sample_policy = {
            'mxs': ['eff.org', '.eff.org'],
            'mode': 'testing'
        }

    def test_merge_keeps_old_mxs(self):
        p = policy.Policy({'mxs': ['eff.org']})
        new_conf = p.merge(policy.Policy({'mxs': ['example.com']}))
        self.assertTrue('eff.org' in new_conf.mxs)
        self.assertTrue('example.com' in new_conf.mxs)

    def test_update_drops_old_mxs(self):
        p = policy.Policy({'mxs': ['eff.org']})
        new_conf = p.update(policy.Policy({'mxs': ['example.com']}))
        self.assertFalse('eff.org' in new_conf.mxs)
        self.assertTrue('example.com' in new_conf.mxs)

    def test_tls_version_default(self):
        p = policy.Policy({})
        self.assertEqual(p.min_tls_version, 'TLSv1.2')

    def test_mode_default(self):
        p = policy.Policy({})
        self.assertEqual(p.mode, 'testing')

    def test_tls_version_valid(self):
        with self.assertRaises(util.ConfigError):
            policy.Policy({'min-tls-version': 'SSLv3'})
        p = policy.Policy({})
        with self.assertRaises(util.ConfigError):
            p.min_tls_version = 'SSLv3'
        p.min_tls_version = 'TLSv1.1'
        self.assertEqual(p.min_tls_version, 'TLSv1.1')

    def test_mode_valid(self):
        p = policy.Policy({})
        with self.assertRaises(util.ConfigError):
            policy.Policy({'mode': 'none'})
        with self.assertRaises(util.ConfigError):
            p.mode = 'none'
        p.mode = 'enforce'
        self.assertEqual(p.mode, 'enforce')

    def test_pins_valid(self):
        p = policy.Policy({}, pinsets={'valid': {}})
        with self.assertRaises(util.ConfigError):
            p.pin = 'invalid'
        with self.assertRaises(util.ConfigError):
            policy.Policy({'pin': 'invalid'}, pinsets={'valid': {}})
        p.pin = 'valid'
        self.assertEqual(p.pin, 'valid')

    def test_alias_valid(self):
        p = policy.Policy({}, aliases={'valid': self.sample_policy})
        with self.assertRaises(util.ConfigError):
            p.policy_alias = 'invalid'
        with self.assertRaises(util.ConfigError):
            policy.Policy({'policy-alias': 'invalid'}, aliases={'valid': self.sample_policy})
        p.policy_alias = 'valid'
        self.assertEqual(p.policy_alias, 'valid')

    def test_mta_sts(self):
        p = policy.Policy({})
        with self.assertRaises(util.ConfigError):
            p.mta_sts = 'yes'
        self.assertFalse(p.mta_sts)
        p.mta_sts = True
        self.assertTrue(p.mta_sts)

    def test_tls_report(self):
        p = policy.Policy({})
        with self.assertRaises(util.ConfigError):
            p.tls_report = False
        p.tls_rpt = 'https://fake.reporting.endpoint'
        self.assertEqual(p.tls_rpt, 'https://fake.reporting.endpoint')

    def test_mxs(self):
        p = policy.Policy({})
        with self.assertRaises(util.ConfigError):
            p.mxs = [True]
        with self.assertRaises(util.ConfigError):
            p.mxs = True
        self.assertEqual(len(p.mxs), 0)
        p.mxs = ['eff.org', '.eff.org']
        self.assertEqual(p.mxs, ['eff.org', '.eff.org'])

    def test_no_alias_policy_setter(self):
        p = policy.PolicyNoAlias({}, aliases={'valid': self.sample_policy})
        with self.assertRaises(util.ConfigError):
            p.policy_alias = 'valid'

    def test_no_alias_policy_getter(self):
        p = policy.PolicyNoAlias({}, aliases={'valid': self.sample_policy})
        self.assertIsNone(p.policy_alias)

if __name__ == '__main__':
    unittest.main()
