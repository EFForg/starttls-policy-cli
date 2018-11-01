"""Various utils used by tests"""

import collections

ParamSet = collections.namedtuple('ParamSet', ('id', 'args', 'kwargs'))

def param(test_name, *args, **kwargs):
    """Convenient wrapper to ParamSet constructor for inline usage in dataset definition."""
    return ParamSet(test_name, args, kwargs)

def parametrize_over(cls, test, data):
    """Iterates over dataset and adds test for each combination of params

    Args:
        cls: TestCase class where tests will be attached.
        test: method of TestCase to parametrize.
        data: List of ParamSet objects, one for each test run.

    Returns:
        None

    """
    for entry in data:
        test_name = "test_" + entry.id
        def _partial(func, *args, **kwargs):
            def wrapped(self):
                return func(self, *args, **kwargs)
            return wrapped
        setattr(cls, test_name, _partial(test, *entry.args, **entry.kwargs))

def assertRaisesRegex(testcase, exc, regex):
    """Portable wrapper for method unittest.TestCase.assertRaisesRegexp which was
    renamed to assertRaisesRegexp in Python 3"""
    try:
        meth = testcase.assertRaisesRegex
    except AttributeError:
        meth = testcase.assertRaisesRegexp
    return meth(exc, regex)
