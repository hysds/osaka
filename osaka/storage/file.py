import urllib.parse
import shutil
import os
import re
import datetime
import io

import osaka.utils
import osaka.base


'''
File handling using local moves and/or fabric 

@author starchmd
'''


class File(osaka.base.StorageBase):
    '''
    File handling for put/gets
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.files = []

    def connect(self, uri, params={}):
        '''
        Connects to the backend
        '''
        osaka.utils.LOGGER.debug("Opening file handler")

    @staticmethod
    def getSchemes():
        '''
        Returns a list of schemes this handler handles
        Note: handling the scheme of another handler produces unknown results
        @returns list of handled schemes
        '''
        return ["", "file"]

    def get(self, uri):
        '''
        Gets the URI (file) as a steam
        @param uri: uri to get
        '''
        if uri.startswith("file:") and not uri.startswith("file:///"):
            raise Exception(
                "Non-absolute paths and non-null hostnames not supported with 'file://' schemed uris")
        osaka.utils.LOGGER.debug("Getting stream from URI: {0}".format(uri))
        fh = open(urllib.parse.urlparse(uri).path, "r")
        self.files.append(fh)
        return fh

    def put(self, stream, uri):
        '''
        Puts a stream to a URI as a steam
        @param stream: stream to upload
        @param uri: uri to put
        '''
        if uri.startswith("file:") and not uri.startswith("file:///"):
            raise Exception(
                "Non-absolute paths and non-null hostnames not supported with 'file://' schemed uris")
        osaka.utils.LOGGER.debug("Putting stream to URI: {0}".format(uri))
        path = urllib.parse.urlparse(uri).path
        try:
            os.makedirs(os.path.dirname(path))
        except Exception as e:
            osaka.utils.LOGGER.debug(
                "Exception while creating directories {0}".format(e))
        flags = 'wb' if isinstance(stream, io.BufferedIOBase) else 'w'
        with open(path, flags) as out:
            shutil.copyfileobj(stream, out)
        return osaka.utils.get_disk_usage(urllib.parse.urlparse(uri).path)

    def size(self, uri):
        '''
        Size the URI (file) as a steam
        @param uri: uri to get
        '''
        if uri.startswith("file:") and not uri.startswith("file:///"):
            raise Exception(
                "Non-absolute paths and non-null hostnames not supported with 'file://' schemed uris")
        osaka.utils.LOGGER.debug("Getting stream from URI: {0}".format(uri))
        return os.path.getsize(urllib.parse.urlparse(uri).path)

    def exists(self, uri):
        '''
        Does the URI exist?
        @param uri: uri to check
        '''
        if uri.startswith("file:") and not uri.startswith("file:///"):
            raise Exception(
                "Non-absolute paths and non-null hostnames not supported with 'file://' schemed uris")
        exts = os.path.exists(urllib.parse.urlparse(uri).path)
        osaka.utils.LOGGER.debug("Does URI {0} exist: {1}".format(uri, exts))
        return exts

    def list(self, uri):
        '''
        List URI
        @param uri: uri to list
        '''
        if uri.startswith("file:") and not uri.startswith("file:///"):
            raise Exception(
                "Non-absolute paths and non-null hostnames not supported with 'file://' schemed uris")
        tmp = urllib.parse.urlparse(uri).path
        if os.path.exists(tmp) and not os.path.isdir(tmp):
            return [tmp]
        return [os.path.join(uri, item) for item in os.listdir(tmp)]

    def isComposite(self, uri):
        '''
        Detect if this uri is a composite uri (uri to collection of objects i.e. directory)
        @param uri: uri to list
        '''
        if uri.startswith("file:") and not uri.startswith("file:///"):
            raise Exception(
                "Non-absolute paths and non-null hostnames not supported with 'file://' schemed uris")
        isDir = os.path.isdir(urllib.parse.urlparse(uri).path)
        osaka.utils.LOGGER.debug(
            "Is URI {0} a directory: {1} {2}".format(uri, isDir, self.exists(uri)))
        return isDir

    def isObjectStore(self): return False

    def close(self):
        '''
        Close this backend
        '''
        osaka.utils.LOGGER.debug("Closing file handler")
        for fh in self.files:
            try:
                fh.close()
            except:
                osaka.utils.LOGGER.debug(
                    "Failed to close file-handle for: {0}".format(fh.name))

    def rm(self, uri):
        '''
        Remove this uri from backend
        @param uri: uri to remove
        '''
        if uri.startswith("file:") and not uri.startswith("file:///"):
            raise Exception(
                "Non-absolute paths and non-null hostnames not supported with 'file://' schemed uris")
        path = urllib.parse.urlparse(uri).path
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


class FileHandlerConversion():
    '''
    This class allows a user to create a file-based approach to handling streams for backends that
    cannot handle their streams independently.
    '''

    def __init__(self, stream):
        '''
        Initialize the class, accepting the stream and creating the temp file if needed
        @param stream: stream to process
        '''
        self.filename = getattr(stream, "name", None)
        self.handler = None
        # If the stream is not a file, make a temporary file out of it
        if self.filename is None or not os.path.exists(self.filename):
            self.handler = File()
            self.filename = "/tmp/osaka-temporary-" + \
                datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S.%f")
            self.handler.connect(self.filename)
            self.handler.put(stream, self.filename)

    def __enter__(self):
        '''
        Return the filename, whither real or temporary
        '''
        return self.filename

    def __exit__(self, exc_type, exc_val, exc_tb):
        '''
        Close the temporary file if it was created
        @param exc_type: unused
        @param exc_val: unused
        @param exc_tb: unused
        '''
        if not self.handler is None:
            self.handler.rm(self.filename)
