""" Tests for configure.py """

import unittest
import tempfile
import os

import mock

from starttls_policy_cli import configure
from starttls_policy_cli.tests.util import param, parametrize_over

class MockGenerator(configure.ConfigGenerator):
    """Mock config generator for testing"""

    def _generate(self, policy_list):
        return "generated_config"

    def _generate_expired_fallback(self, policy_list):
        return "#expired_fallback"

    def _instruct_string(self):
        return "instruct_string"

    @property
    def mta_name(self):
        return "fake"

    @property
    def default_filename(self):
        return "default_filename"

class TestConfigGenerator(unittest.TestCase):
    """Test the base config generator class"""
    def test_generate(self):
        with TempPolicyDir(test_json) as testdir:
            generator = MockGenerator(testdir)
            generator.generate()
            pol_filename = os.path.join(testdir, generator.default_filename)
            with open(pol_filename) as pol_file:
                result = pol_file.read()
            os.remove(pol_filename)
        self.assertEqual(result, "generated_config\n")

    def test_manual_instructions(self):
        with TempPolicyDir(test_json) as testdir:
            generator = MockGenerator(testdir)
            with mock.patch("starttls_policy_cli.configure.six.print_") as mock_print:
                generator.manual_instructions()
                mock_print.assert_called_once_with("\n"
                    "--------------------------------------------------\n"
                    "Manual installation instructions for fake\n"
                    "--------------------------------------------------\n"
                    "instruct_string")


class TempPolicyDir(object):
    # pylint: disable=useless-object-inheritance,attribute-defined-outside-init
    """This context manager creates temporary directory
    and writes given policy into it."""
    def __init__(self, conf):
        self._conf = conf

    def __enter__(self):
        self._tmpdir = tempfile.mkdtemp()
        self._policy_filename = os.path.join(self._tmpdir, 'policy.json')
        with open(self._policy_filename, 'w') as pol_file:
            pol_file.write(self._conf)
        return self._tmpdir

    def __exit__(self, exc_type, exc_value, traceback):
        os.remove(self._policy_filename)
        os.rmdir(self._tmpdir)

test_json = '{\
    "author": "Electronic Frontier Foundation",\
    "timestamp": "2018-06-18T09:41:50.264201364-07:00",\
    "expires": "2038-01-16T09:41:50.264201364-07:00",\
        "policies": {\
            ".valid.example-recipient.com": {\
                "mode": "enforce",\
                "mxs": [".valid.example-recipient.com"]\
            },\
            ".testing.example-recipient.com": {\
                "mode": "testing",\
                "mxs": [".testing.example-recipient.com"]\
            }\
        }\
    }'

test_json_expired = '{\
    "author": "Electronic Frontier Foundation",\
    "timestamp": "2018-06-18T09:41:50.264201364-07:00",\
    "expires": "2018-07-16T09:41:50.264201364-07:00",\
        "policies": {\
            ".valid.example-recipient.com": {\
                "mode": "enforce",\
                "mxs": [".valid.example-recipient.com"]\
            },\
            ".testing.example-recipient.com": {\
                "mode": "testing",\
                "mxs": [".testing.example-recipient.com"]\
            }\
        }\
    }'

testgen_data = [
    param("simple_policy", test_json, "# .testing.example-recipient.com "
                                      "undefined due to testing policy\n"
                                      ".valid.example-recipient.com    "
                                      "secure match=.valid.example-recipient.com\n"),
    param("expired_policy", test_json_expired, "# Policy list is outdated. "
                                               "Falling back to opportunistic encryption.\n"),
]

class TestPostfixGenerator(unittest.TestCase):
    """Test Postfix config generator"""

    def test_mta_name(self):
        generator = configure.PostfixGenerator("./")
        self.assertEqual(generator.mta_name, "Postfix")

    def test_instruct_string(self):
        generator = configure.PostfixGenerator("./")
        instructions = generator._instruct_string() # pylint: disable=protected-access
        self.assertTrue("postmap" in instructions)
        self.assertTrue("postconf -e \"smtp_tls_policy_maps=" in instructions)
        self.assertTrue("postfix reload" in instructions)
        self.assertTrue(generator.default_filename in instructions)

    def config_test(self, conf, expected):
        """PostfixGenerator test parameterized over various policies"""
        with TempPolicyDir(conf) as testdir:
            generator = configure.PostfixGenerator(testdir)
            generator.generate()
            pol_filename = os.path.join(testdir, generator.default_filename)
            with open(pol_filename) as pol_file:
                result = pol_file.read()
            os.remove(pol_filename)
        self.assertEqual(result, expected)

parametrize_over(TestPostfixGenerator, TestPostfixGenerator.config_test, testgen_data)

if __name__ == "__main__":
    unittest.main()
