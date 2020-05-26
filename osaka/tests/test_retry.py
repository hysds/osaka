from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()


"""
Created on Oct 31, 2016

@author: mstarch
"""


# TODO: fix unit tests for circleci

# class RetryTest(unittest.TestCase):
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
#    def test_retry(self):
#        '''
#        Timeout and ensure that there error
#        '''
#        for obj in self.ins:
#            self.cleanup()
#            # Removes affect of any caches, etc.
#            try:
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#            except:
#                pass
#            # Time one run
#            time0 = time.time()
#            try:
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
#            except:
#                pass
#            time0 = time.time() - time0
#            # Time 10 retries
#            time1 = time.time()
#            try:
#                osaka.main.get(obj, self.scratch, {
#                               "timeout": 0.00000001}, retries=100)
#            except:
#                pass
#            time1 = time.time() - time1
#            # Make sure it is at least 10 times longer
#            osaka.utils.LOGGER.info(
#                "Time0: {0} Time1: {1}:".format(time0, time1))
#            self.assertTrue(
#                time1/time0 >= 9, "Retry didn't occur enough {0} vs {1}".format(time1/time0, 10))
