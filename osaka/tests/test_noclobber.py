from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()


"""
Created on Aug, 2017

@author: mstarch
"""


# TODO: fix unit tests for circleci

# class NoClobberTest(unittest.TestCase):
#    '''
#    A test that tries the rmall function.
#    '''
#
#    def setUp(self):
#        '''
#        Setup method for the test case
#        '''
#        self.config = osaka.tests.util.load_test_config()
#        self.addCleanup(self.cleanup)
#        unittest.TestCase.setUp(self)
#        self.scratch = self.config.get("scratch_file")
#        self.worker = self.config.get("dav", {}).get("worker", None)
#        # A list of input objects from various locations
#        self.ins = [self.config.get("http", {}).get("test_input_urls", [])[0]]
#        # A list of output only locations
#        self.out = []
#        # Construct path to checked-in test cases
#        self.base = os.path.dirname(osaka.__file__)+"/../resources/objects/"
#        self.objects = [os.path.join(self.base, listing) for listing in os.listdir(
#            self.base) if listing.startswith("test-")]
#        osaka.tests.util.scpWorkerObject(self, self.objects[1])
#        self.assertTrue(self.scratch.startswith("/tmp/osaka"),
#                        "Assertion Error: scratch space is un-safe")
#        # Clean up old temp directories and create new ones
#        try:
#            osaka.main.rmall(self.scratch, unlock=True)
#        except OSError as e:
#            if not str(e).startswith("[Errno 2]"):
#                raise
#        os.makedirs(self.scratch)
#
#    def cleanup(self):
#        '''
#        Cleanup existing directories
#        '''
#        try:
#            osaka.main.rmall(self.scratch, unlock=True)
#        except OSError as e:
#            if not str(e).startswith("[Errno 2]"):
#                raise
#        return True
#
#    def test_clobber(self):
#        '''
#        Timeout and ensure that there error
#        '''
#        for obj in self.ins:
#            # Removes affect of any caches, etc.
#            osaka.main.get(obj, self.scratch)
#            osaka.main.get(obj, self.scratch)
#            with self.assertRaises(osaka.utils.NoClobberException):
#                osaka.main.get(obj, self.scratch, noclobber=True)
#            with self.assertRaises(osaka.utils.NoClobberException):
#                osaka.main.put(obj, self.scratch, noclobber=True)
