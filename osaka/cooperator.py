from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from future import standard_library
standard_library.install_aliases()
import copy
import time
from osaka.utils import OsakaException, CooperationNotPossibleException


class Cooperator(object):
    '''
    A cooperator object used to facilitate cooperation between two differen osaka instances
    @mstarch
    '''

    def __init__(self, source, dlock, lockMetadata):
        '''
        Initialize a cooperator
        '''
        self.source = source
        self.dlock = dlock
        self.lockMetadata = lockMetadata
        self.primary = False

    def __enter__(self):
        '''
        Enter this cooperate block
        @param:
        '''
        # Atomic lock-or-cooperate depends on each backend's atomicity of "put"
        try:
            lockMetadata = copy.copy(self.lockMetadata)
            lockMetadata["source"] = self.source
            self.dlock.lock(lockMetadata)
            self.primary = True
        except OsakaException as ose:
            if not "Lock file already locked" in ose:
                raise
            self.whenLocked()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        '''
        Handle exceptions in the with block
        @param exception_type: exception type
        @param exception_value: exception value
        @param traceback: traceback of exception
        '''
        if not self.primary:
            return
        elif not exception_value is None:
            self.dlock.setLockMetadata("error", str(
                exception_type) + str(exception_value))
        else:
            self.dlock.unlock()

    def whenLocked(self):
        '''
        What to do when a file is already locked
        '''
        ex_source = self.dlock.getLockMetadata("source")
        error = self.dlock.getLockMetadata("error")
        ouri = self.dlock.ouri
        if ex_source is None:
            raise CooperationNotPossibleException("No source specified. Cooperation not possible for {0}"
                                                  .format(ouri))
        elif self.source != ex_source:
            raise CooperationNotPossibleException("{0} differs incoming source {1}. Cooperation not possible for {2}"
                                                  .format(self.source, ex_source, ouri))
        elif not error is None:
            raise OsakaException(
                "Cooperation error for {0}: {1}".format(ouri, error))

    def isPrimary(self):
        '''
        Is this the primary responsible for download
        '''
        return self.primary


class Spinner(object):
    '''
    A class to spin on a download
    @author mstarch
    '''

    def __init__(self, dlock, timeout, interval=0.5):
        '''
        Initialize this spinner
        @param dlock: lock to spin on
        '''
        self.dlock = dlock
        self.timeout = timeout
        self.interval = interval

    def spin(self):
        '''
        Will spin on this lock until download completes or error is detected
        '''
        tm = 0
        while True:
            error = self.dlock.getLockMetadata("error")
            if not error is None:
                raise OsakaException("Cooperation error: " + error)
            elif not self.dlock.isLocked():
                return
            elif self.timeout != -1 and tm > self.timeout:
                raise OsakaException("Timed out after {0} seconds".format(tm))
            time.sleep(self.interval)
            tm = tm + self.interval
