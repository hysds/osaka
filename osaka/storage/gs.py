from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from future import standard_library

standard_library.install_aliases()
import re
from google.cloud import storage
from google.cloud.exceptions import NotFound
import urllib.parse
from io import StringIO

import osaka.base
import osaka.utils
import osaka.storage.file

"""
google storage connection service
@author starchmd,gmanipon
"""


class GS(osaka.base.StorageBase):
    """
    Handles GS file copies
    """

    def __init__(self):
        """
        Constructor
        """
        self.files = []

    def connect(self, uri, params={}):
        """
        Connects to the backend
        @param uri - gs uri for resource
        @param params - optional, may contain: location
        """
        osaka.utils.LOGGER.debug("Opening GS handler")
        uri = re.compile("^gs").sub("http", uri)
        parsed = urllib.parse.urlparse(uri)
        session_kwargs = {}
        kwargs = {}
        parsed.hostname if "location" not in params else params["location"]
        if parsed.hostname is not None:
            kwargs["endpoint_url"] = "%s://%s" % (parsed.scheme, parsed.hostname)
        else:
            kwargs["endpoint_url"] = "%s://%s" % (parsed.scheme, kwargs["endpoint_url"])
        if parsed.port is not None:
            kwargs["endpoint_url"] = "%s:%s" % (kwargs["endpoint_url"], parsed.port)
        if parsed.username is not None:
            session_kwargs["gcp_access_key_id"] = parsed.username
        elif "gcp_access_key_id" in params:
            session_kwargs["gcp_access_key_id"] = params["gcp_access_key_id"]
        if parsed.password is not None:
            session_kwargs["gcp_secret_access_key"] = parsed.password
        elif "gcp_secret_access_key" in params:
            session_kwargs["gcp_secret_access_key"] = params["gcp_secret_access_key"]
        kwargs["use_ssl"] = parsed.scheme == "https"

        container, key = osaka.utils.get_container_and_path(parsed.path)
        session_kwargs["profile_name"] = container
        self.gs = storage.Client()

    @staticmethod
    def getSchemes():
        """
        Returns a list of schemes this handler handles
        Note: handling the scheme of another handler produces unknown results
        @returns list of handled schemes
        """
        return ["gs"]

    def get(self, uri):
        """
        Gets the URI as a stream
        @param uri: uri to get
        """
        osaka.utils.LOGGER.debug("Getting stream from URI: {0}".format(uri))
        container, key = osaka.utils.get_container_and_path(
            urllib.parse.urlparse(uri).path
        )
        bucket = self.bucket(container, create=False)
        blob = bucket.blob(key)
        stream = StringIO(blob.download_as_string())
        return stream

    def put(self, stream, uri):
        """
        Puts a stream to a URI as a stream
        @param stream: stream to upload
        @param uri: uri to put
        """
        osaka.utils.LOGGER.debug("Putting stream to URI: {0}".format(uri))
        container, key = osaka.utils.get_container_and_path(
            urllib.parse.urlparse(uri).path
        )
        bucket = self.bucket(container)
        CHUNK_SIZE = 2147221504  # Bytes
        blob = bucket.blob(key, chunk_size=CHUNK_SIZE)
        with osaka.storage.file.FileHandlerConversion(stream) as fn:
            blob.upload_from_filename(fn)
        return blob.size

    def size(self, uri):
        """
        Get the size of this object
        """
        osaka.utils.LOGGER.debug("Getting size from URI: {0}".format(uri))
        container, key = osaka.utils.get_container_and_path(
            urllib.parse.urlparse(uri).path
        )
        bucket = self.bucket(container, create=False)
        blob = bucket.blob(key)
        raise blob.size

    def listAllChildren(self, uri):
        """
        List all children of the current uri
        @param uri: uri to check
        """
        osaka.utils.LOGGER.debug("Running list all children")
        parsed = urllib.parse.urlparse(uri)
        container, key = osaka.utils.get_container_and_path(parsed.path)
        bucket = self.bucket(container, create=False)
        collection = bucket.list_blobs(prefix=key)
        uriBase = (
            parsed.scheme
            + "://"
            + parsed.hostname
            + (":" + str(parsed.port) if parsed.port is not None else "")
        )
        return [
            uriBase + "/" + container + "/" + item.name
            for item in collection
            if item.name == key or item.name.startswith(key + "/")
        ]

    def exists(self, uri):
        """
        Does the URI exist?
        @param uri: uri to check
        """
        osaka.utils.LOGGER.debug("Does URI {0} exist?".format(uri))
        # A key exists if it has some children
        return len(self.listAllChildren(uri)) > 0

    def list(self, uri):
        """
        List URI
        @param uri: uri to list
        """
        depth = len(uri.rstrip("/").split("/"))
        return [
            item
            for item in self.listAllChildren()
            if len(item.rstrip("/").split("/")) == (depth + 1)
        ]

    def isComposite(self, uri):
        """
        Detect if this uri is a composite uri (uri to collection of objects i.e. directory)
        @param uri: uri to list
        """
        osaka.utils.LOGGER.debug("Is URI {0} a directory".format(uri))
        children = self.listAllChildren(uri)
        if len(children) == 0 or (len(children) == 1 and children[0] == uri):
            return False
        return True

    def isObjectStore(self):
        return True

    def close(self):
        """
        Close this backend
        """
        osaka.utils.LOGGER.debug("Closing GS handler")

    def rm(self, uri):
        """
        Remove this uri from backend
        @param uri: uri to remove
        """
        container, key = osaka.utils.get_container_and_path(
            urllib.parse.urlparse(uri).path
        )
        bucket = self.bucket(container, create=False)
        bucket.delete_blob(key)

    def getKeysWithPrefixURI(self, uri):
        """
        Keys with prefix of given URI
        @param uri: prefix URI
        """
        parsed = urllib.parse.urlparse(uri)
        container, key = osaka.utils.get_container_and_path(parsed.path)
        bucket = self.bucket(container, create=False)
        collection = bucket.list_blobs(prefix=key)
        return [item.bucket_name + "/" + item.name for item in collection]

    def bucket(self, bucket, create=True):
        """
        Gets the given bucket or makes it
        @param bucket - name of bucket to find
        """
        try:
            return self.gs.get_bucket(bucket)
        except NotFound:
            return self.gs.create_bucket(bucket)
