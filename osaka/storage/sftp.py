from __future__ import print_function

import os
import os.path
import stat
import urlparse
import paramiko
'''
A backend used to handle stfp using parimiko

@author starchmd
'''
class SFTP(object):
    '''
     SFTP handling for Osaka
    '''
    def __init__(self,params={}):
        '''
        Constructor
        '''
        self.keyfile = params["keyfile"] if "keyfile" in params else None
    def connect(self,host=None,port=None,user=None,password=None,secure=False):
        '''
        Connect to this storage medium.  All data is parsed out of the url and may be None
            scheme:
        @param host - may be None, host to connect to
                      implementor must handle defaulting
        @param port - may be None, port to connect to
                      implementor must handle a None port
        @param user - may be None, user to connect as
                      implementor must handle a None user
        @param password - may be None, password to connect with
                      implementor must handle a None password
        '''
        self.client = paramiko.client.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(host,port=22 if port is None else int(port),username=user,password=password,key_filename=self.keyfile,timeout=15)
        self.sftp = self.client.open_sftp()
    
    @classmethod
    def getSchemes(clazz):
        '''
        Returns a list of schemes this handler handles
        Note: handling the scheme of another handler produces unknown results
        @returns list of handled schemes
        '''
        return ["sftp"]
    def put(self,path,url):
        '''
        Put the given path to the given url
        @param path - local path of file/folder to put
        @param url - url to put file/folder to
        '''
        rpath = urlparse.urlparse(url).path.lstrip("/")
        print("\n\n\n\nUploading:",path);
        if not os.path.isdir(path):
            print("As file");
            try:
                self.sftp.mkdir(os.path.dirname(rpath))
            except IOError as e:
                pass 
            dest = rpath
            try:
                if stat.S_ISDIR(self.sftp.stat(rpath).st_mode) != 0:
                    dest = os.path.join(rpath,os.path.basename(path))
            except:
                pass
            return self.upload(path,dest)    
        print("As Dir");
        try:
            self.sftp.mkdir(rpath)
        except IOError as e:
            pass 
        for dirpath, dirname, filenames in os.walk(path):
            extra = os.path.relpath(dirpath,os.path.dirname(path))
            try:
                self.sftp.mkdir(os.path.join(rpath,extra))
            except IOError as e:
                pass
            for filename in filenames:
                self.upload(os.path.join(dirpath,filename),os.path.join(rpath,extra,filename))
    def upload(self,path,rpath):
        '''
        Uploads a file to remote path
        @param path - path to upload
        @param rpath - remote path to upload to
        '''
        self.sftp.put(path,rpath)
        return True
    def get(self,url,path):
        '''
        Get the url (file/folder) to local path
        @param url - url to get file/folder from
        @param path - path to place fetched files
        '''
        rpath = urlparse.urlparse(url).path
        self.sftp.get(rpath,path)
    def rm(self,url):
        '''
        Remove the item
        @param url - url to remove
        '''
        rpath = urlparse.urlparse(url).path
        self.sftp.remove(rpath)
    def close(self):
        '''
        Close this connection
        '''
        self.client.close()
