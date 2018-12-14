import re
import azure.common
import urlparse
import datetime
import os.path
import json
import osaka.base
import osaka.utils 
import osaka.storage.file

from azure.storage.blob import BlockBlobService

'''
Azure storage connection services
@author starchmd
'''
class Azure(osaka.base.StorageBase):
    '''
    A class used to connect to the Azure storage and
    upload/download files using blob storage
    '''
    def __init__(self):
        '''
        Constructor for the Azure object

        '''
        self.tmpfiles = []
        self.service = None
    def connect(self,uri,params={}):
        '''
        Connect to the Azure service with given user and key
        @param user - username to use to connect to
        @param key - key to use to connect
        '''
        osaka.utils.LOGGER.debug("Opening Azure handler")
        self.cache = {}
        uri = re.compile("^azure").sub("http",uri)
        parsed = urlparse.urlparse(uri)
        session_kwargs = {}
        kwargs = {}
        check_host = parsed.hostname if not "location" in params else params["location"]
        if not parsed.hostname is None:
            kwargs["endpoint_url"] = "%s://%s" % (parsed.scheme, parsed.hostname)
        else:
            kwargs["endpoint_url"] = "%s://%s" % (parsed.scheme, kwargs["endpoint_url"])
        if not parsed.port is None and parsed.port != 80 and parsed.port != 443:
            kwargs["endpoint_url"] = "%s:%s" % (kwargs["endpoint_url"], parsed.port)
        if not parsed.username is None:
            session_kwargs["account_name"] = parsed.username
        elif "account_name" in params:
            session_kwargs["account_name"] = params["account_name"]
        if not parsed.password is None:
            session_kwargs["account_key"] = parsed.password
        elif "account_key" in params:
            session_kwargs["account_key"] = params["account_key"]
        kwargs["use_ssl"] = parsed.scheme == "https"

        self.service = BlockBlobService(**session_kwargs)

        if self.service is None:
            raise osaka.utils.OsakaException("Failed to connect to Azure")

    @staticmethod
    def getSchemes():
        '''
        Returns a list of schemes this handler handles
        Note: handling the scheme of another handler produces unknown results
        @returns list of handled schemes
        '''
        return ["azure","azures"]
    def get(self, uri):
        '''
        Gets the URI (azure or azures) as a steam
        @param uri: uri to get
        '''
        osaka.utils.LOGGER.debug("Getting stream from URI: {0}".format(uri))
        container,key = osaka.utils.get_container_and_path(urlparse.urlparse(uri).path)
        fname = "/tmp/osaka-azure-"+str(datetime.datetime.now())
        with open(fname,"w"):
            pass
        fh = open(fname,"r+b")
        self.tmpfiles.append(fh)
        self.service.get_blob_to_bytes(container, key, fh)
        fh.seek(0)
        return fh
    def put(self, stream, uri):
        '''
        Puts a stream to a URI as a steam
        @param stream: stream to upload
        @param uri: uri to put
        '''
        osaka.utils.LOGGER.debug("Putting stream to URI: {0}".format(uri))
        container,key = osaka.utils.get_container_and_path(urlparse.urlparse(uri).path)
        self.service.create_container(container)
        with osaka.storage.file.FileHandlerConversion(stream) as fn:
            self.service.create_blob_from_stream(container, key, fn)
        properties = self.service.get_blob_properties(container, key)

        return properties.content_length
    def listAllChildren(self,uri):
        '''
        List all children of the current uri
        @param uri: uri to check
        '''
        osaka.utils.LOGGER.debug("Running list all children")
        ret = []
        #Dump the cache if possible
        if "__top__" in self.cache and uri == self.cache["__top__"]:
            return [ k for k in self.cache.keys() if k != "__top__" ]
        parsed = urlparse.urlparse(uri)
        container,key = osaka.utils.get_container_and_path(parsed.path)
        #key in this instance is used as a prefix to be filtered out.
        collection = self.service.list_blobs(container, key)
        uriBase = parsed.scheme+"://"+parsed.hostname + (":"+str(parsed.port) if not parsed.port is None else "")
        #Setup cache, and fill it with listings
        self.cache["__top__"] = uri
        for item in collection:
            if not (item.key == key or item.key.startswith(key+"/") or key == ""):
                continue
            full = uriBase +"/"+ item.name + "/" + item.key
            self.cache[full] = item
            ret.append(full)
        return ret
    def exists(self,uri):
        '''
        Does the URI exist?
        @param uri: uri to check
        '''
        osaka.utils.LOGGER.debug("Does URI {0} exist?".format(uri))
        #A key exists if it has some children
        return len(self.listAllChildren(uri)) > 0
    def list(self,uri):
        '''
        List URI
        @param uri: uri to list
        '''
        depth = len(uri.rstrip("/").split("/"))
        return [item for item in self.listAllChildren() if len(item.rstrip("/").split("/")) == (depth + 1)] 
    def isComposite(self,uri):
        '''
        Detect if this uri is a composite uri (uri to collection of objects i.e. directory)
        @param uri: uri to list
        '''
        osaka.utils.LOGGER.debug("Is URI {0} a directory".format(uri))
        children = self.listAllChildren(uri)
        if len(children) == 0 or (len(children) == 1 and children[0] == uri):
            return False
        return True
    def isObjectStore(self): return True
    def close(self):
        '''
        Close this backend
        '''
        osaka.utils.LOGGER.debug("Closing Azure handler")
        for fh in self.tmpfiles:
            try:
                fh.close()
            except:
                osaka.utils.LOGGER.debug("Failed to close temporary file-handle for: {0}".format(fh.name))
            try:
                os.remove(fh.name) 
            except:
                osaka.utils.LOGGER.debug("Failed to remove temporary file-handle for: {0}".format(fh.name))

    def size(self,uri):
        '''
        Size this uri from backend
        @param uri: uri to size
        '''
        if uri in self.cache:
            return self.cache[uri].size
        container,key = osaka.utils.get_container_and_path(urlparse.urlparse(uri).path)
        properties = self.service.get_blob_properties(cont, blob)
        return properties.content_length
    def rm(self,uri):
        '''
        Remove this uri from backend
        @param uri: uri to remove
        '''
        container,key = osaka.utils.get_container_and_path(urlparse.urlparse(uri).path)
        for b in self.service.list_blobs(cont,prefix=blob):
            self.service.delete_blob(cont,b.name)

    def getKeysWithPrefixURI(self,uri):
        '''
        Keys with prefix of given URI
        @param uri: prefix URI
        '''
        parsed = urlparse.urlparse(uri)
        container,key = osaka.utils.get_container_and_path(parsed.path)
        collection = self.service.list_blobs(container, key)
        return [item.name + "/" + item.key for item in collection]
