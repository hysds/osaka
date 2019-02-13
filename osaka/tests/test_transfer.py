from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from future import standard_library
standard_library.install_aliases()
import re
import os
import copy
import subprocess
import unittest

import osaka.main
import osaka.tests.util

# Turn off requests warning
import requests
requests.packages.urllib3.disable_warnings()
'''
Created on Aug 29, 2016

@author: mstarch
'''


class TransferTest(unittest.TestCase):
    '''
    A test that flushes out standard transfer functions between all backends.
    Performs the cross-product between the inputs and the outputs.
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
        self.file = self.config.get("tmp_file", "/tmp/osaka-unittest-objects/")
        self.worker = self.config.get("dav", {}).get("worker", None)
        # A list of input objects from various locations
        self.ins = []
        # A list of backends supporting both incoming and
        # outgoing product, and thus can be setup internal
        # to this test
        self.inouts = []
        for section in list(self.config.values()):
            try:
                self.ins.extend(section.get("test_input_urls", []))
                self.inouts.extend(section.get("test_output_urls", []))
            except AttributeError as aee:
                pass
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
        try:
            osaka.main.rmall(self.file)
        except OSError as e:
            if not str(e).startswith("[Errno 2]"):
                raise
        os.makedirs(self.scratch)
        os.makedirs(self.file)

    def cleanup(self):
        '''
        Cleanup existing directories
        '''
        try:
            osaka.main.rmall(self.scratch, unlock=True)
        except OSError as e:
            if not str(e).startswith("[Errno 2]"):
                raise
        try:
            osaka.main.rmall(self.file)
        except OSError as e:
            if not str(e).startswith("[Errno 2]"):
                raise
        return True

    def test_InOuts(self, callback=None):
        '''
        A test running against all in-out capable backends
        @param callback: additional code to run per-remote object (for bigger tests)
        '''
        objs = []
        # For every input-output backend
        for inout in self.inouts:
            osaka.utils.LOGGER.info(
                "Running In-Out Test for {0}".format(inout))
            objs = self.uploadInputObjects(inout)
            # Test downloading
            for remote in objs:
                osaka.main.get(remote, self.scratch)
                loc = os.path.join(self.scratch, os.path.basename(remote))
                self.assertTrue(self.checkObject(
                    loc), "Downloaded product inconsistent with original product: {0}".format(loc))
                # Run submitted code, if supplied
                if not callback is None:
                    callback(loc, remote)
                # Cleanup external
                osaka.main.rmall(remote)
                osaka.main.rmall(loc)

    def test_InOutExists(self):
        '''
        A test to ensure that, if a directory, re-transferring to existing location creates a child directory, and if
        a file, it replaces the file.
        '''
        scratch = os.path.join(self.scratch, "redownload")
        os.makedirs(scratch)

        def reupload(download, remote):
            '''
            Re-uploads the supplied object and checks that
            the dowloaded object is consistent with the tested behavior.
            @param download: downloaded object
            @param remote: remote object
            '''
            osaka.main.transfer(download, remote)
            osaka.main.transfer(remote, scratch)
            if not os.path.isdir(download):
                self.checkObject(os.path.join(
                    scratch, os.path.basename(remote)))
            else:
                self.checkObject(os.path.join(
                    scratch, os.path.basename(remote), os.path.basename(remote)))
            osaka.main.rmall(scratch)
        # First run the in-out tests
        self.test_InOuts(reupload)

    def test_Criscross(self, extras=[]):
        '''
        Tests the cross product of inputs and outputs to test every permutation of in to out.
        @param extras: extra (external) files to add as inputs into the base criscross test
        '''
        uploads = []
        noquery = re.compile("\?[^?]*")
        # For every output backend
        for inout in self.inouts:
            try:
                osaka.utils.LOGGER.info(
                    "Running Criscross Test for {0}".format(inout))
                uploads = self.uploadInputObjects(inout)
                objs = copy.copy(uploads)
                objs.extend(extras)
                dest = os.path.join(inout, "output-objects")
                # For each input, transfer it to the
                for remote in objs:
                    final = os.path.join(dest, os.path.basename(remote))
                    final = noquery.sub("", final)
                    osaka.main.transfer(remote, final)
                    osaka.main.transfer(final, self.scratch)
                    loc = noquery.sub("", os.path.join(
                        self.scratch, os.path.basename(remote)))
                    self.assertTrue(self.checkObject(
                        loc), "Downloaded product inconsistent with original product: {0}".format(loc))
                    osaka.main.rmall(loc)
                # Cleanup
                osaka.main.rmall(dest)
            finally:
                try:
                    osaka.main.rmall(os.path.join(inout, "input-objects"))
                except:
                    pass

    def test_CriscrossWithExternal(self):
        '''
        Tests the cross product of inputs and outputs to test every permutation of in to out.
        Note: adds extra input only products
        '''
        self.test_Criscross(self.ins)

    def checkObject(self, obj):
        '''
        Checks an object in against the original object contained in the Osaka module
        @param obj - object to test (by name) against original
        '''
        return subprocess.call(["diff", "-r", os.path.join(self.base, os.path.basename(obj), obj), obj], stdout=osaka.tests.util.DEVNULL, stderr=osaka.tests.util.DEVNULL) == 0

    def uploadInputObjects(self, uriBase):
        '''
        Upload all input products, safely, to end-point. Places them in directory "input-objects"
        @param uriBase: base uri to upload to
        @return: set of uploaded products
        '''
        output = []
        dest = os.path.join(uriBase, "input-objects")
        for obj in self.objects:
            self.assertFalse(osaka.main.exists(os.path.join(dest, os.path.basename(
                obj))), "Destination {0} already exists, test cannot safely continue.".format(dest))
            osaka.main.put(obj, os.path.join(dest, os.path.basename(obj)))
            output.append(os.path.join(dest, os.path.basename(obj)))
        return output
