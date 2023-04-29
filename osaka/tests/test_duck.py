from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()
import unittest
import inspect
import osaka.base


class DuckTest(unittest.TestCase):
    """
    This class runs against all Osaka storage backends, making sure that they
    meet all the necessary requirements to be Osaka storage backends.
    """

    def test_ModuleDuckTypeing(self):
        """
        Tests the duck-typing of the Osaka storage modules
        """
        definitions = {
            "__init__": ["self"],
            "getSchemes": [],
            "connect": ["self", "uri", "params"],
            "get": ["self", "uri"],
            "put": ["self", "stream", "uri"],
            "listAllChildren": ["self", "uri"],
            "exists": ["self", "uri"],
            "list": ["self", "uri"],
            "isComposite": ["self", "uri"],
            "close": ["self"],
            "rm": ["self", "uri"],
            "size": ["self", "uri"],
        }
        # Loop through the classes found by loading the backends and
        # ensure they are up-to-spec
        sb = osaka.base.StorageBase()
        for scheme, clazz in sb.loadBackends().items():
            # Loop through all definitions making sure they exist in the specification
            for func, values in definitions.items():
                try:
                    attr = getattr(clazz, func)
                except AttributeError:
                    self.assertTrue(
                        False,
                        "{0} does not have function: {1}".format(clazz.__name__, func),
                    )
                (
                    args,
                    varargs,
                    keywords,
                    defaults,
                    kwonlyargs,
                    kwonlydefaults,
                    annotations,
                ) = inspect.getfullargspec(attr)
                # Remove defaulted arguments if possible
                if args is not None and defaults is not None:
                    count = len(args) - len(defaults)
                    tmp = args[:count]
                    # Add back in any defined, but defaulted values
                    for arg in args[count:]:
                        if arg in values:
                            tmp.append(arg)
                    args = tmp
                # Go through list of required arguments
                self.assertEqual(
                    args,
                    values,
                    "{0}.{1} has invalid arguments: {2} vs {3}".format(
                        clazz.__name__, attr.__name__, values, args
                    ),
                )
