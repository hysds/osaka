'''
An Osaka backend that connects to ftp
@author mstarch
'''
import re
import urllib.parse
import datetime
import os.path
import json
import osaka.base
import osaka.utils 
import osaka.storage.file

import netrc
import ftplib

class FTP(osaka.base.StorageBase):
    '''
    An FTP connecion class used to connect to the FTP servers
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.tmpfiles = []
    def connect(self,uri,params={}):
        '''
        Connects to the backend, given the URI
        @param uri - ftp uri to connect to
        @param params - optional, parameters for the connection
        '''
        parsed = urllib.parse.urlparse(uri)
        netloc = parsed.netloc
        username = parsed.username
        password = parsed.password
        #If we were not supplied a username or password, seek it in the netrc
        if username is None or password is None:
            rchandle = netrc.netrc()
            username, account, password = rchandle.authenticators(netloc)
        osaka.utils.LOGGER.info("Logging into {0} with ({1})".format(netloc, username))
        self.ftp = ftplib.FTP(netloc, username, password) 
        #self.ftp.login()
        osaka.utils.LOGGER.debug("Successfully logged in")
    @staticmethod
    def getSchemes():
        '''
        Returns a list of schemes this handler handles
        Note: handling the scheme of another handler produces unknown results
        @returns list of handled schemes
        '''
        return ["ftp"]
    def get(self,uri):
        '''
        Gets the URI ftp as a steam
        @param uri: uri to get
        '''
        osaka.utils.LOGGER.debug("Getting stream from URI: {0}".format(uri))
        filename = urllib.parse.urlparse(uri).path
        fname = "/tmp/osaka-ftp-"+str(datetime.datetime.now())
        with open(fname, "w") as tmpf:
            self.ftp.retrbinary('RETR %s' % filename, tmpf.write)
        fh = open(fname,"r+b")
        self.tmpfiles.append(fh)
        fh.seek(0)
        return  fh #obj.get()["Body"]
    def put(self,stream,uri):
        '''
        Puts a stream to a URI as a steam
        @param stream: stream to upload
        @param uri: uri to put
        '''
        raise OsakaException("Not implemented; implementation deferred")
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
        parsed = urllib.parse.urlparse(uri)
        filename = parsed.path
        listing = self.ftp.nlst(filename)
        base = parsed.netloc if parsed.netloc.endswith("/") else parsed.netloc + "/" 
        listing = [parsed.scheme + "://" +base + item.lstrip("/") for item in listing]
        return listing
    def isComposite(self,uri):
        '''
        Detect if this uri is a composite uri (uri to collection of objects i.e. directory)
        @param uri: uri to list
        '''
        osaka.utils.LOGGER.debug("Is URI {0} a directory".format(uri))
        children = self.list(uri)
        if len(children) == 0 or (len(children) == 1 and children[0] == uri):
            return False
        return True
    def isObjectStore(self): return False
    def close(self):
        '''
        Close this backend
        '''
        osaka.utils.LOGGER.debug("Closing ftp handler")
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
        filename = urllib.parse.urlparse(uri).path
        return self.size(filename) 
    def rm(self,uri):
        '''
        Remove this uri from backend
        @param uri: uri to remove
        '''
        raise OsakaException("Not implemented; implementation deferred")
