from __future__ import print_function
import os
import re
import urlparse
import requests
import easywebdav
import datetime

from requests.auth import HTTPBasicAuth,HTTPDigestAuth

import osaka.utils
import osaka.base
import osaka.storage.file
import osaka.storage.http

requests.packages.urllib3.disable_warnings()
'''
WebDav Handler

Osaka handler for the webdav backend services.  

Note: easywebdav is not used in all functions, as it assumes that the "PROPFIND" command is permitted
and on some workers, it is not. Thus, this backend uses the HTTP backend internally

@author starchmd
'''
class DAV(osaka.base.StorageBase):
    '''
    Http and WebDav handling backends
    '''
    def __init__(self):
        '''
        Constructor
        '''
        pass
    def connect(self,uri,params={}):
        '''
        Connects to the backend
        '''
        osaka.utils.LOGGER.debug("Opening WebDav handler")
        #Grab information out of the URI
        username,password = osaka.utils.get_uri_username_and_password(uri)
        scheme,host = osaka.utils.get_uri_scheme_and_hostname(uri)
        #Setup webdav connection
        self.webdav = easywebdav.connect(host, username=username, password=password,protocol=re.compile("^dav").sub("http",scheme), verify_ssl=False)
        self.httpHandler = osaka.storage.http.HTTP()
        self.httpHandler.connect(re.compile("^dav").sub("http",uri), params)
    @staticmethod
    def getSchemes():
        '''
        Returns a list of schemes this handler handles
        Note: handling the scheme of another handler produces unknown results
        @returns list of handled schemes
        '''
        return ["dav","davs"]
    def get(self,uri,text=False):
        '''
        Gets the URI (file) as a steam
        @param uri: uri to get
        @param text: should we pull out text data instead of raw
        '''
        osaka.utils.LOGGER.debug("Getting stream to URI: {0} Note: Using HTTP GET".format(uri))
        #Use the standard HTTP handler for getting the product
        return self.httpHandler.get(re.compile("^dav").sub("http",uri),text=text)
    def put(self,stream,uri):
        '''
        Puts a stream to a URI as a steam
        @param stream: stream to upload
        @param uri: uri to put
        '''
        osaka.utils.LOGGER.debug("Putting stream to URI: {0}".format(uri))
        path = osaka.utils.get_uri_path(uri)
        #Attempt to create the directories needed
        try:
            self.webdav.mkdirs(os.path.dirname(path))
            self.webdav.delete(path)
        except Exception as e:
            osaka.utils.LOGGER.debug("Exception making directories and cleaning up existing product: {0}".format(e))
        #Create a filename to handle this stream
        with osaka.storage.file.FileHandlerConversion(stream) as fn:
            #Handle zero-length separately from webdav
            if os.path.getsize(fn) == 0:
                self.httpHandler.session.put(re.compile("^dav").sub("http",uri),"",verify=False,timeout=self.httpHandler.timeout).raise_for_status()
            else:
                self.webdav.upload(fn,path)
        #Get size for put item
        response = self.httpHandler.session.head(re.compile("^dav").sub("http",uri),verify=False,timeout=self.httpHandler.timeout)
        response.raise_for_status()
        return int(response.headers["Content-Length"])
    def size(self, uri):
        '''
        Size of object
        '''
        osaka.utils.LOGGER.debug("Size stream to URI: {0} Note: Using HTTP size".format(uri))
        #Use the standard HTTP handler for getting the product
        return self.httpHandler.size(re.compile("^dav").sub("http",uri),text=text)
    def exists(self,uri):
        '''
        Does the URI exist?
        @param uri: uri to check
        '''
        osaka.utils.LOGGER.debug("Does URI {0} exist?".format(uri))
        try:
            path = osaka.utils.get_uri_path(uri)
            tmp = self.webdav.exists(path)
            osaka.utils.LOGGER.debug("Does URI {0} exist? {1}".format(uri,tmp))
            return tmp
        except Exception as e:
            pass
        osaka.utils.LOGGER.debug("Failed to check existence using HEAD")
        try:
            text = self.httpHandler.get(re.compile("^dav").sub("http",uri),text=True)
            if re.search("\s*(?:<!DOCTYPE)|(?:<!doctype)",text):
                raise osaka.utils.OsakaException("Unauthorized, redirected to login")
            osaka.utils.LOGGER.debug("Does URI {0} exist? {1}".format(uri,True))
            return True
        except Exception as e:
            if "404 Client Error:" in str(e):
                osaka.utils.LOGGER.debug("Does URI {0} exist? {1}".format(uri,False))
                return False
            raise
    def list(self,uri):
        '''
        List URI
        @param uri: uri to list
        '''
        reg = re.compile("^http")
        return [reg.sub("dav",uri) for uri in self.httpHandler.list(re.compile("^dav").sub("http",uri))]
    def isComposite(self,uri):
        '''
        Detect if this uri is a composite uri (uri to collection of objects i.e. directory)
        @param uri: uri to list
        '''
        return self.httpHandler.isComposite(re.compile("^dav").sub("http",uri))
    def isObjectStore(self): return False
    def close(self):
        '''
        Close this backend
        '''
        osaka.utils.LOGGER.debug("Closing DAV handler")
        self.httpHandler.close()
    def rm(self,uri):
        '''
        Remove this uri from backend
        @param uri: uri to remove
        '''
        path = osaka.utils.get_uri_path(uri)
        try:
            osaka.utils.LOGGER.debug("Removing {0} as a file".format(uri))
            self.webdav.delete(path)
        except Exception as e:
            osaka.utils.LOGGER.debug("Removing {0} as a directory, file encountered error {1}".format(uri,e))
            self.webdav.rmdir(path)

