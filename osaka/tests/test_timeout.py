from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from future import standard_library
standard_library.install_aliases()
import os
import copy
import subprocess
import unittest
import requests.exceptions

import osaka.main
import osaka.tests.util
'''
Created on Oct 31, 2016

@author: mstarch
'''


class TimeoutTest(unittest.TestCase):
    '''
    A test that setus up high and low timeouts to ensure that the timeouts
    work properly.
    '''

    def setUp(self):
        '''
        Setup method for the test case
        '''
        self.config = osaka.tests.util.load_test_config()
        self.addCleanup(self.cleanup)
        unittest.TestCase.setUp(self)
        self.scratch = self.config.get(
            "scratch_file", "/tmp/osaka-unittest-scratch/")
        self.worker = self.config.get("dav", {}).get("worker", None)
        # A list of input objects from various locations
        self.ins = [self.config.get("dav", {}).get("test_input_urls", [])[0],
                    self.config.get("http", {}).get("test_input_urls", [])[0]
                    ]
        # A list of output only locations
        self.out = []
        # Construct path to checked-in test cases
        self.base = os.path.dirname(osaka.__file__)+"/../resources/objects/"
        self.objects = [os.path.join(self.base, listing) for listing in os.listdir(
            self.base) if listing.startswith("test-")]
        osaka.tests.util.scpWorkerObject(self, self.objects[1])
        self.assertTrue(self.scratch.startswith("/tmp/osaka"),
                        "Assertion Error: scratch space is un-safe")
        # Clean up old temp directories and create new ones
        try:
            osaka.main.rmall(self.scratch, unlock=True)
        except OSError as e:
            if not str(e).startswith("[Errno 2]"):
                raise
        os.makedirs(self.scratch)

    def cleanup(self):
        '''
        Cleanup existing directories
        '''
        try:
            osaka.main.rmall(self.scratch, unlock=True)
        except Exception as e:
            pass
        except OSError as e:
            if not str(e).startswith("[Errno 2]"):
                raise
        return True

    def test_timeout(self):
        '''
        Timeout and ensure that there error
        '''
        for obj in self.ins:
            self.cleanup()
            with self.assertRaises(requests.exceptions.Timeout):
                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})

    def test_notimeout(self):
        '''
        Timeout and ensure that there error
        '''
        for obj in self.ins:
            self.cleanup()
            try:
                osaka.main.get(obj, self.scratch, {"timeout": 1000})
            except requests.exceptions.Timeout as te:
                self.assertFalse(True, "Timeout recieved when not intended")
