""" Tests for util.py """
import unittest
from functools import partial
import datetime
from dateutil import tz

from starttls_policy_cli import util
from starttls_policy_cli.tests.util import param, parametrize_over

class TestEnforceUtil(unittest.TestCase):
    """ Unittests for "enforcer" functions."""

    def test_enforce_in(self):
        array = ["a", "b", "c", "d"]
        func = partial(util.enforce_in, array)
        self.assertEqual(func("a"), "a")
        with self.assertRaises(util.ConfigError):
            func(["a"])
        with self.assertRaises(util.ConfigError):
            func("e")
        with self.assertRaises(util.ConfigError):
            func(0)

    def test_enforce_type(self):
        func = partial(util.enforce_type, int)
        with self.assertRaises(util.ConfigError):
            func("a")
        self.assertEqual(func(1), 1)

    def test_enforce_list(self):
        func = partial(util.enforce_list, partial(util.enforce_type, int))
        with self.assertRaises(util.ConfigError):
            func(["a", 2])
        self.assertEqual(func([0, 1]), [0, 1])

    def test_enforce_fields(self):
        func = partial(util.enforce_fields, partial(util.enforce_type, int))
        self.assertEqual(func({"a": 0, "b": 1}), {"a": 0, "b": 1})

    def test_enforce_bad_fields(self):
        func = partial(util.enforce_fields, partial(util.enforce_type, int))
        self.assertRaises(util.ConfigError, func, {"b": "a", "c": 2})

    def test_parse_bad_datestring(self):
        self.assertRaises(util.ConfigError, util.parse_valid_date, "fake")

    def parse_valid_date_test(self, valid_date, expected):
        """Parametrized test for util.parse_valid_date function"""
        self.assertEqual(util.parse_valid_date(valid_date), expected)

    def is_expired_test(self, expiration, expected):
        """Parametrized test for util.is_expired function"""
        self.assertEqual(util.is_expired(expiration), expected)

parametrize_over(TestEnforceUtil, TestEnforceUtil.parse_valid_date_test,
                 [
                    param("valid_datetime_date",
                          datetime.datetime(1970, 1, 1, 0, 0, tzinfo=tz.tzutc()),
                          datetime.datetime(1970, 1, 1, 0, 0, tzinfo=tz.tzutc())),
                    param("valid_integer_date",
                          0,
                          datetime.datetime(1970, 1, 1, 0, 0, tzinfo=tz.tzutc())),
                    param("valid_string_date",
                          "2014-05-26T01:35:33+00:00",
                          datetime.datetime(2014, 5, 26, 1, 35, 33, tzinfo=tz.tzutc())),
                    param("valid_string_date_notz",
                          "2014-05-26T01:35:33",
                          datetime.datetime(2014, 5, 26, 1, 35, 33, tzinfo=tz.tzutc())),
                    param("valid_string_date_nocolon",
                          "2014-05-26T01:35:33+0000",
                          datetime.datetime(2014, 5, 26, 1, 35, 33, tzinfo=tz.tzutc())),
                 ])

parametrize_over(TestEnforceUtil, TestEnforceUtil.is_expired_test,
                 [
                    param("expired",
                          datetime.datetime(1970, 1, 1, 0, 0, tzinfo=tz.tzutc()),
                          True),
                    param("nonexpired",
                          datetime.datetime(2038, 1, 1, 0, 0, tzinfo=tz.tzutc()),
                          False),
                 ])

if __name__ == '__main__':
    unittest.main()
