import os
import json
import copy
import time
import subprocess
import unittest
import requests.exceptions

import osaka.main
import osaka.tests.util
'''
Created on July 27, 2017

@author: mstarch
'''


class LockfileTest(unittest.TestCase):
    '''
    A test that attempts to ensure that the lockfiles are being created and
    with the correct standards. That is:
      1. Lockfile is made during transfer
      2. Lockfile records "source"
      3. Lockfile is collaborated on
    '''

    def setUp(self):
        '''
        Setup method for the test case
        '''
        self.config = osaka.tests.util.load_test_config()
        self.addCleanup(self.cleanup)
        unittest.TestCase.setUp(self)
        self.scratch = self.config.get("scratch_file")
        self.worker = self.config.get("dav", {}).get("worker", None)
        # A list of input objects from various locations
        self.ins = [self.config.get("http", {}).get("test_input_urls", [])[0]]
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
        self.lockfile = self.scratch.rstrip("/") + "/{0}.osaka.locked.json"
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
            # pass
            osaka.main.rmall(self.scratch, unlock=True)
        except OSError as e:
            if not str(e).startswith("[Errno 2]"):
                raise
        return True

    def test_lock_source(self):
        '''
        Timeout and ensure that there error
        '''
        for obj in self.ins:
            base = os.path.basename(obj)
            # Timeout transfer, creating a locked file
            try:
                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
            except Exception as ose:
                pass
            # Open json file and read out data
            lock = osaka.lock.Lock(os.path.join(
                self.scratch, os.path.basename(obj)))
            self.assertTrue(os.path.exists(self.lockfile.format(
                base)), "Lockfile {0} does not exist".format(self.lockfile.format(base)))
            self.assertTrue(lock.isLocked(), "Lock does not report locked")
            with open(self.lockfile.format(base)) as fp:
                data = json.load(fp)
            self.assertEqual(data.get("source", None), obj,
                             "Lockfile source not correct")
            self.assertEqual(lock.getLockMetadata("source"),
                             obj, "Lock source not correct")
            # Check timeout error
            self.assertNotEqual(data.get("error", None), None, "Error not set")
            self.assertNotEqual(lock.getLockMetadata(
                "error"), None, "Error not set")

    def test_collaborate_and_error(self):
        '''
        Test that osaka collaborate will return the error found with another instance
        '''
        for obj in self.ins:
            # Timeout transfer, creating a locked file
            try:
                osaka.main.rmall(self.scratch, unlock=True)
                osaka.main.rmall(self.lockfile.format(os.path.basename(obj)))
            except Exception as ose:
                pass
            try:
                osaka.main.get(obj, self.scratch, {"timeout": 0.00000001})
            except Exception as ose:
                pass
            lock = osaka.lock.Lock(self.scratch)
            # Report the same error
            try:
                osaka.main.get(obj, self.scratch)
                self.assertFalse(
                    True, "No error thrown when cooperating on an errored download")
            except Exception as exc:
                exp_error = lock.getLockMetadata("error")
                exp_error = "dsakhldsalkjsdaasd" if exp_error is None else exp_error
                self.assertTrue(exp_error in str(
                    exc), "Error {0} not found in cooperation error {1}".format(exp_error, str(exc)))
            # Osaka refuses to collaborate
            self.lockfile = self.scratch.rstrip("/") + ".osaka.locked.json"
            with open(self.lockfile) as fp:
                data = json.load(fp)
            del data["error"]
            with open(self.lockfile, "w") as fp:
                json.dump(data, fp)
            with self.assertRaises(osaka.utils.CooperationRefusedException):
                osaka.main.get(obj, self.scratch, ncoop=True,
                               params={"timeout": 2})
            with self.assertRaises(osaka.utils.CooperationNotPossibleException):
                osaka.main.get("/tmp/asdlkjsadl", self.scratch)
