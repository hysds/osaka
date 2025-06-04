"""
Created on Apr 27, 2016

@author: mstarch
"""

from future import standard_library

standard_library.install_aliases()
import urllib.parse
import osaka.utils


class StorageBase(object):
    """
    Represents the base class for Osaka storage implementers
    including basic functions.
    """

    def __init__(self, params={}):
        """
        Constructor
        """
        self.connect(params)

    @classmethod
    def getStorageBackend(clazz, uri):
        """
        Returns a subclass instance of this class that
        can process the given URI type
        @param uri: uri for which to get a backend
        """
        clazz.loadBackends()
        scheme = urllib.parse.urlparse(uri).scheme
        try:
            return clazz.map[scheme]()
        except KeyError:
            # Try with the other protocol (http/https)
            if scheme == 'https':
                scheme = 'http'
            elif scheme == 'http':
                scheme = 'https'
            try:
                return clazz.map[scheme]()
            except KeyError:
                err = "No backend found for scheme: {0}".format(scheme)
                osaka.utils.LOGGER.error(err)
                raise osaka.utils.OsakaException(err)
        except Exception as e:
            err = "Failed to get backend for {0}. Reason: {1}".format(scheme, e)
            osaka.utils.LOGGER.error(err)
            raise osaka.utils.OsakaException(err)

    @classmethod
    def loadBackends(clazz):
        """
        Loads the backends
        """
        if "map" in clazz.__dict__:
            return
        clazz.map = {}
        import osaka.storage.file
        import osaka.storage.http
        import osaka.storage.webdav
        import osaka.storage.s3
        import osaka.storage.az
        import osaka.storage.gs
        import osaka.storage.ftp

        for cls in clazz.__subclasses__():
            types = cls.getSchemes()
            osaka.utils.LOGGER.debug(
                "Found storage backend: {0} handling {1}".format(cls.__name__, types)
            )
            for scheme in types:
                clazz.map[scheme] = cls
        return clazz.map

    def connect(self, params={}):
        """
        Connects to the backend
        """
        raise osaka.utils.OsakaException(
            "{0} does not implement 'connection' call".format(type(self).__name__)
        )

    def get(self, uri):
        """
        Gets the URI as a steam
        @param uri: uri to get
        """
        raise osaka.utils.OsakaException(
            "{0} does not implement 'get' call".format(type(self).__name__)
        )

    def put(self, stream, uri):
        """
        Puts a stream to a URI as a steam
        @param stream: stream to upload
        @param uri: uri to put
        """
        raise osaka.utils.OsakaException(
            "{0} does not implement 'put' call".format(type(self).__name__)
        )

    def exists(self, uri):
        """
        Does the URI exist?
        @param uri: uri to check
        """
        raise osaka.utils.OsakaException(
            "{0} does not implement 'exists' call".format(type(self).__name__)
        )

    def list(self, uri):
        """
        List URI
        @param uri: uri to list
        """
        raise osaka.utils.OsakaException(
            "{0} does not implement 'list' call".format(type(self).__name__)
        )

    def isComposite(self, uri):
        """
        Detect if this uri is a composite uri (uri to collection of objects i.e. directory)
        @param uri: uri to list
        """
        raise osaka.utils.OsakaException(
            "{0} does not implement 'isComposite' call".format(type(self).__name__)
        )

    def isObjectStore(self):
        """
        Return True if backend is an object store where no directories exist. Only keys.
        @param uri: uri to list
        """
        raise osaka.utils.OsakaException(
            "{0} does not implement 'isObjectStore' call".format(type(self).__name__)
        )

    def close(self):
        """
        Close this backend
        """
        raise osaka.utils.OsakaException(
            "{0} does not implement 'close' call".format(type(self).__name__)
        )

    def rm(self, uri):
        """
        Remove this uri from backend
        @param uri: uri to remove
        """
        raise osaka.utils.OsakaException(
            "{0} does not implement 'rm' call".format(type(self).__name__)
        )

    def listAllChildren(self, uri):
        """
        List all children of the current uri, including this URI if it is a non-composite
        @param uri: uri to check
        """
        osaka.utils.LOGGER.debug(
            "{0} does not implement 'listAllChildren' call, attempting list-and-walk".format(
                type(self).__name__
            )
        )
        children = []
        for entry in self.list(uri):
            if self.isComposite(entry):
                children.extend(self.listAllChildren(entry))
            else:
                children.append(entry)
        return children
