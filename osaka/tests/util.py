from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()
import os
import json
import logging
import subprocess

logging.basicConfig(level=logging.ERROR)

# Discard output
try:
    from subprocess import DEVNULL  # py3k
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')


def load_test_config():
    '''
    Load a test configuration
    '''
    with open(os.path.join(os.path.dirname(__file__), "test.json")) as fp:
        return json.load(fp)


def scpWorkerObject(self, obj):
    '''
    '''
    ret = subprocess.call(
        ["scp", "-r", obj, self.worker+":/data/work/"], stdout=DEVNULL, stderr=DEVNULL)
    if ret != 0:
        raise Exception("Failed to SCP input to WebDav worker")
