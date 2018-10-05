def parameterized(func):
    """Partially applies params to function so it can be added
    as test method to unittest.TestCase class"""
    def applied_params(*args, **kwargs):
        def class_method(self):
            return func(self, *args, **kwargs)
        return class_method
    return applied_params

def parameterize_over(cls, test, data):
    """Links parameter-ready tests with its dataset"""
    for entry in data:
        tname, args = entry[0], entry[1:]
        test_name = "test_" + tname
        wrapped_test = test(*args)
        setattr(cls, test_name, wrapped_test)
