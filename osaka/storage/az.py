from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import open
from builtins import str
from future import standard_library

standard_library.install_aliases()
import re
import urllib.parse
import datetime
import os.path
import traceback
from uuid import uuid4

import osaka.base
import osaka.utils
import osaka.storage.file

from configparser import ConfigParser
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

"""
Azure storage connection services
@author starchmd,zanechua,andiariffin,d3lta-v
"""


class Azure(osaka.base.StorageBase):
    """
    A class used to connect to the Azure storage and upload/download
    files using blob storage
    """

    def __init__(self):
        """
        Constructor for the Azure object
        """
        self.tmpfiles = []
        self.client = None
        self.account_name = None
        self.account_key = None
        self.connection_string = None
        self.container_name = None

    def connect(self, uri, params={}):
        """
        Connects to the backend
        @param uri - azures or azure uri for resource
        @param params - optional, may contain: account_name, account_key, connection_string
        """
        osaka.utils.LOGGER.debug("Opening Azure handler")
        self.cache = {}
        
        # Parse account name and key from params or environment
        self.account_name = params.get('account_name')
        self.account_key = params.get('account_key')
        self.connection_string = params.get('connection_string')
        
        # If no credentials provided, try to use DefaultAzureCredential
        if not (self.account_name and self.account_key) and not self.connection_string:
            try:
                self.client = BlobServiceClient(
                    account_url=f"https://{self.account_name}.blob.core.windows.net",
                    credential=DefaultAzureCredential()
                )
                osaka.utils.LOGGER.debug("Successfully authenticated with DefaultAzureCredential")
            except Exception as e:
                osaka.utils.LOGGER.warning(
                    "Failed to authenticate with DefaultAzureCredential: {}".format(str(e))
                )
        
        # If still no client, try with account key or connection string
        if self.client is None:
            if self.connection_string:
                self.client = BlobServiceClient.from_connection_string(self.connection_string)
                osaka.utils.LOGGER.debug("Connected using connection string")
            elif self.account_name and self.account_key:
                self.client = BlobServiceClient(
                    account_url=f"https://{self.account_name}.blob.core.windows.net",
                    credential={"account_name": self.account_name, "account_key": self.account_key}
                )
                osaka.utils.LOGGER.debug("Connected using account name and key")
            else:
                raise osaka.utils.OsakaException(
                    "No valid Azure credentials provided. Need either account_name/account_key or connection_string."
                )
        
        # Extract container name from URI
        parsed = urllib.parse.urlparse(uri)
        self.container_name = parsed.netloc.split('.')[0]  # Extract container name from hostname
        uri = re.compile("^azure").sub("http", uri)
        parsed = urllib.parse.urlparse(uri)
        session_kwargs = {}

        # attempt to get account_name (as username) from url or parameters array
        if parsed.username is not None:
            session_kwargs["account_name"] = parsed.username
        elif "account_name" in params:
            session_kwargs["account_name"] = params["account_name"]

        # attempt to get account_key (as password) from url or parameters array
        if parsed.password is not None:
            session_kwargs["account_key"] = parsed.password
        elif "account_key" in params:
            session_kwargs["account_key"] = params["account_key"]

        # if neither account_name or account_key is populated, fallback to
        # directly parsing configuration file in ~/.azure
        if "account_name" not in session_kwargs or "account_key" not in session_kwargs:
            # check if ~/.azure/config exists
            azure_config_path = os.environ["HOME"] + "/.azure/config"
            if os.path.isfile(azure_config_path):
                azure_config = ConfigParser()
                azure_config.read(azure_config_path)
                session_kwargs["account_name"] = azure_config.get("storage", "account")
                session_kwargs["account_key"] = azure_config.get("storage", "key")
            else:
                raise osaka.utils.OsakaException(
                    "No Azure Blob Storage credentials found at " + azure_config_path
                )

    def _get_service(self):
        """
        For backward compatibility, returns the client
        """
        return self.client

    @staticmethod
    def getSchemes():
        """
        Returns a list of schemes this handler handles
        Note: handling the scheme of another handler produces unknown results
        @returns list of handled schemes
        """
        return ["azure", "azures"]

    def get(self, uri):
        """
        Gets the URI (azures or azure) as a stream
        @param uri: uri to get
        """
        osaka.utils.LOGGER.debug("Getting stream from URI: {0}".format(uri))
        container_name, blob_name = self._extract_container_and_blob(uri)
        
        # Create a temporary file to store the blob
        fname = "/tmp/osaka-azure-%s-%s" % (uuid4(), datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S.%f"))
        try:
            # Get a blob client
            blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
            
            # Download the blob to a temporary file
            with open(fname, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            # Open the file for reading and add to tmpfiles for cleanup
            fh = open(fname, "rb")
            self.tmpfiles.append(fh)
            return fh
        except Exception as e:
            osaka.utils.LOGGER.error("Failed to get blob: {0}".format(str(e)))
            if os.path.exists(fname):
                os.remove(fname)
            raise

    def put(self, stream, uri):
        """
        Puts a stream to a URI as a stream
        @param stream: stream to upload
        @param uri: uri to put
        """
        osaka.utils.LOGGER.debug("Putting stream to URI: {0}".format(uri))
        container_name, blob_name = self._extract_container_and_blob(uri)
        
        # Create container if it doesn't exist
        container_client = self.client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()
        
        # Create a temporary file to store the stream
        with osaka.storage.file.FileHandlerConversion(stream) as fn:
            # Upload the file
            with open(fn, "rb") as data:
                blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
                blob_client.upload_blob(data, overwrite=True)
        
        # Get the blob properties to return the content length
        try:
            blob_props = blob_client.get_blob_properties()
            return blob_props.size
        except Exception as e:
            osaka.utils.LOGGER.warning("Failed to get blob properties: {0}".format(str(e)))
            return 0

    def listAllChildren(self, uri):
        """
        List all children of the current uri
        @param uri: uri to check
        """
        osaka.utils.LOGGER.debug("Running list all children")
        ret = []
        # Dump the cache if possible
        if "__top__" in self.cache and uri == self.cache["__top__"]:
            return [k for k in list(self.cache.keys()) if k != "__top__"]
        parsed = urllib.parse.urlparse(uri)
        container_name, blob_name = self._extract_container_and_blob(uri)
        # blob_name in this instance is used as a prefix to be filtered out.
        collection = self.client.list_blobs(container_name, blob_name)
        uriBase = (
            parsed.scheme
            + "://"
            + parsed.hostname
            + (":" + str(parsed.port) if parsed.port is not None else "")
        )
        # Setup cache, and fill it with listings
        self.cache["__top__"] = uri
        for item in collection:
            if not (item.name == blob_name or item.name.startswith(blob_name + "/") or blob_name == ""):
                continue
            full = uriBase + "/" + container_name + "/" + item.name
            self.cache[full] = item
            ret.append(full)
        return ret

    def exists(self, uri):
        """
        Does the URI exist?
        @param uri: uri to check
        """
        try:
            container_name, blob_name = self._extract_container_and_blob(uri)
            blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
            return blob_client.exists()
        except Exception as e:
            osaka.utils.LOGGER.error("Failed to check if blob exists: {0}".format(str(e)))
            return False

    def list(self, uri):
        """
        List URI
        @param uri: uri to list
        """
        depth = len(uri.rstrip("/").split("/"))
        return [
            item
            for item in self.listAllChildren(uri)
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
        osaka.utils.LOGGER.debug("Closing Azure handler")
        for fh in self.tmpfiles:
            try:
                fh.close()
            except Exception as e:
                osaka.utils.LOGGER.debug("Failed to close temporary file-handle for {0}: {1}".format(fh.name, str(e)))
            try:
                if os.path.exists(fh.name):
                    os.remove(fh.name)
            except Exception as e:
                osaka.utils.LOGGER.debug("Failed to remove temporary file {0}: {1}".format(fh.name, str(e)))
        
        # Close the client connection
        if hasattr(self, 'client') and self.client is not None:
            try:
                self.client.close()
            except Exception as e:
                osaka.utils.LOGGER.debug("Failed to close Azure client: {0}".format(str(e)))

    def size(self, uri):
        """
        Size this uri from backend
        @param uri: uri to size
        """
        if uri in self.cache:
            return self.cache[uri].size
        container_name, blob_name = self._extract_container_and_blob(uri)
        blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
        properties = blob_client.get_blob_properties()
        return properties.size

    def rm(self, uri):
        """
        Remove this uri from backend
        @param uri: uri to remove
        """
        container_name, blob_name = self._extract_container_and_blob(uri)
        blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.delete_blob()

    def _extract_container_and_blob(self, uri):
        """
        Extracts container and blob name from URI
        @param uri: Azure blob storage URI
        @return: tuple of (container_name, blob_name)
        """
        parsed = urllib.parse.urlparse(uri)
        path = parsed.path.lstrip('/')
        
        # Handle both formats: container.blob.core.windows.net/... and azure://container/...
        if parsed.netloc and '.blob.core.windows.net' in parsed.netloc:
            # Format: https://container.blob.core.windows.net/blob/path
            container = parsed.netloc.split('.')[0]
            return container, path
        else:
            # Format: azure://container/blob/path
            parts = path.split('/', 1)
            if len(parts) == 1:
                return parts[0], ""
            return parts[0], parts[1]

    def getKeysWithPrefixURI(self, uri):
        """
        Keys with prefix of given URI
        @param uri: prefix URI
        """
        container_name, prefix = self._extract_container_and_blob(uri)
        container_client = self.client.get_container_client(container_name)
        blobs = container_client.list_blobs(name_starts_with=prefix)
        return [f"{blob.name}" for blob in blobs]
