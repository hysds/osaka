from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from builtins import str
from future import standard_library

standard_library.install_aliases()
import os
import json
import socket
import traceback

# Py2k-3k imports
try:
    import urllib.urlparse as urlparse
except ImportError:
    import urllib.parse as urlparse
try:
    import io as io
except:
    import io
# Osaka imports
import osaka.base
import osaka.utils

# Lock file metadata basics
try:
    HOST_FQDN = socket.getfqdn()
except:
    osaka.utils.LOGGER.warning("Failed to get FQDN, setting to 'unknown'")
    HOST_FQDN = "unknown"
try:
    PID = str(os.getpid())
except:
    osaka.utils.LOGGER.warning("Failed to get PID, setting to 'unknown'")
    PID = "unknown"
INTERLOCK_NAME_TEMPLATE = "{0}.osaka.locked.json"

WTF_CNT = 0


class Lock(object):
    """
    A class to handle the lock file/URIs used by osaka. Simply hand it an
    Osaka URI to begin.
    @author mstarch
    """

    def __init__(self, ouri, handle=None, params={}):
        """
        Construct this lock object locking the give osaka-uri
        @param ouri: osaka uri for lock-handling
        @param handle: osaka handle for this lock file, if None specifiy params
        @param params: parameters for handle creation, if {} or None specify handle
        """
        self.ouri = ouri
        self.handle = handle
        self.params = params
        self.luri = Lock.getLockUri(self.ouri)
        self.secret = "Justin is an amazing person! Perhaps wax-sculpture worthy."
        # self.lockExtras = {}
        self.locked = False

    def lock(self, lockMetadata={}):
        """
        Lock the object represented by this file
        @param lockMetadata: metadata to stick
        """
        osaka.utils.LOGGER.debug("Locking {0} with {1}".format(self.ouri, self.luri))
        tmp = {"pid": PID, "hostname": HOST_FQDN, "osaka-lock-secret": self.secret}
        tmp.update(lockMetadata)
        # tmp.update(self.lockExtras)
        stream = io.StringIO(str(json.dumps(tmp)))
        with PermTemp(self.luri, self.handle, self.params) as handle:
            # Not perfect exception
            if handle.exists(self.luri):
                raise osaka.utils.OsakaException("Lock file already locked")
            handle.put(stream, self.luri)
        self.locked = True

    def unlock(self):
        """
        Unlock the object represented by this object
        """
        osaka.utils.LOGGER.debug("Unlocking {0} with {1}".format(self.ouri, self.luri))
        with PermTemp(self.luri, self.handle, self.params) as handle:
            handle.rm(self.luri)
        self.locked = False

    def getLockMetadata(self, field):
        """
        Get a field out of the lock-uri metadata
        @param field: field to read from the lock-uri
        @return: lock-uri field
        """
        osaka.utils.LOGGER.debug(
            "Looking for {0} in lock-uri {1}".format(field, self.luri)
        )
        with PermTemp(self.luri, self.handle, self.params) as handle:
            try:
                filelike = handle.get(self.luri)
                return json.load(filelike).get(field, None)
            except Exception as e:
                osaka.utils.LOGGER.warning(
                    "Ignoring encountered exception: {}\n{}".format(
                        e, traceback.format_exc()
                    )
                )
                return None

    def setLockMetadata(self, field, value):
        """
        Get a field out of the lock-uri metadata
        @param field: field to read from the lock-uri
        @param value: value to set
        """
        osaka.utils.LOGGER.debug(
            "Looking for {0} in lock-uri {1}".format(field, self.luri)
        )
        #        if not self.locked:
        #            self.lockExtras[field] = value
        #            return
        with PermTemp(self.luri, self.handle, self.params) as handle:
            filelike = handle.get(self.luri)
            jsn = json.load(filelike)
            jsn[field] = value
            stream = io.StringIO(json.dumps(jsn))
            handle.put(stream, self.luri)

    def isLocked(self):
        """
        Check to see if the URI is locked
        """
        osaka.utils.LOGGER.info(
            "Checking lock status of {0} in {1}".format(self.ouri, self.luri)
        )
        if self.locked:
            return self.locked
        try:
            return self.getLockMetadata("osaka-lock-secret") == self.secret
        except:
            return False

    @staticmethod
    def getLockUri(ouri):
        """
        Gets the lockfile uri from the given ouri
        @param ouri: osaka-uri to wrap with the lock
        """
        parsed = urlparse.urlparse(ouri)
        parsed = parsed._replace(
            path=INTERLOCK_NAME_TEMPLATE.format(parsed.path.rstrip("/"))
        )
        return parsed.geturl()


class PermTemp(object):
    """
    A permanent or temporary wrapper for a handle. Allows the "with" clause to close if and only
    if we made a temporary handle
    @author mstarch
    """

    def __init__(self, luri, handle=None, params={}):
        """
        Initialize a new perm-temp object
        """
        self.luri = luri
        if handle is None:
            self.close = True
            osaka.utils.LOGGER.debug(
                "Opening handler for lock-uri {0}".format(self.luri)
            )
            self.handle = osaka.base.StorageBase.getStorageBackend(self.luri)
            self.handle.connect(self.luri, params)
            return
        self.handle = handle
        self.close = False

    def __enter__(self):
        """
        Enter function 
        """
        return self.handle

    def __exit__(self, exception_type, exception_value, traceback):
        """
        Exit function
        """
        if self.close:
            self.handle.close()
