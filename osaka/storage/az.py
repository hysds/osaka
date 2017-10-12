import os.path
import urlparse
from azure.storage.blob import BlobService
from osaka.utils import get_container_and_path,walk,OsakaException

'''
Azure storage connection services
@author starchmd
'''
class Azure(object):
    '''
    A class used to connect to the Azure storage and
    upload/download files using blob storage
    '''
    def __init__(self,params={}):
        '''
        Constructor for the Azure object

        '''
        if "user" in params:
            self.user = params["user"]
        else:
            self.user = None
        if "key" in params:
            self.key = params["key"]
        else:
            self.key = None
    def connect(self, host, port, user, password, secure):
        '''
        Connect to the Azure service with given user and key
        @param user - username to use to connect to
        @param key - key to use to connect
        '''
        kwargs = {}
        err = None
        if not host is None:
            kwargs["host_base"] = "."+host
        if not user is None:
            kwargs["account_name"] = user
        elif not self.user is None:
            kwargs["account_name"] = self.user
        if not password is None:
            kwargs["account_key"] = password
        elif not self.key is None:
            kwargs["account_key"] = self.key
        kwargs["protocol"] = "https" if secure else "http"
        try:
            self.service = BlobService(**kwargs)
        except Exception as e:
            err = e.message
            self.service = None
        if self.service is None:
            raise OsakaException("Failed to connect to Azure:"+("" if err is None else err))
    @classmethod
    def getSchemes(clazz):
        '''
        Returns a list of schemes this handler handles
        Note: handling the scheme of another handler produces unknown results
        @returns list of handled schemes
        '''
        return ["azure","azures"]
    def close(self):
        '''
        Close this service
        '''
        pass
    def put(self, path, url):
        '''
        Put a file up to the cloud
        @param path - path to upload
        @param url - path in cloud to upload too
        '''
        if os.path.isdir(path):
            return walk(self.put,path,url)
        cont,blob = get_container_and_path(urlparse.urlparse(url).path)
        self.service.create_container(cont)
        self.service.put_block_blob_from_path(cont,blob,path)
        return True
    def get(self, url, dest):
        '''
        Get file(s) from the cloud
        @param url - url on cloud to pull down (on cloud)
        @param dest - dest to download too
        '''
        cont,blob = get_container_and_path(urlparse.urlparse(url).path)
        for b in self.service.list_blobs(cont,prefix=blob):
            destination=os.path.join(dest,os.path.relpath(b.name,blob)) if blob != b.name else dest
            if not os.path.exists(os.path.dirname(destination)):
                os.mkdir(os.path.dirname(destination))
            self.service.get_blob_to_path(cont,b.name,destination)
        return True
    def rm(self,url):
        '''
        Remove this url and all children urls
        @param url - url to remove
        '''
        cont,blob = get_container_and_path(urlparse.urlparse(url).path)
        for b in self.service.list_blobs(cont,prefix=blob):
            self.service.delete_blob(cont,b.name)
        return True
