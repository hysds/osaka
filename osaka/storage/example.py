from __future__ import print_function
'''
Example of a storage handler used with Osaka.
parsed from the url:
    <scheme>://[<username>:<password>@]<hostname>:<port>/<path>

@author starchmd
'''
class Example(object):
    '''
    Example Osaka handler
    '''
    def __init__(self,params={}):
        '''
        Constructor:
            1. All parameters are in the params map
            2. Remember, this is called often 
               and called long before "connect"
        '''
        print("Init the example handler")
    def connect(self,host,port,user,password,secure):
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
        print("Connecting to example handler:",host,port,user,password,secure)
    @classmethod
    def getSchemes(clazz):
        '''
        Returns a list of schemes this handler handles
        Note: handling the scheme of another handler produces unknown results
        @returns list of handled schemes
        '''
        return ["example","examples"]
    def put(self,path,url):
        '''
        Put the given path to the given url
        @param path - local path of file to put
        @param url - url to put file/folder to
        '''
        print("Putting:",path,"to",url)
        return False
    def get(self,url,dest):
        '''
        Get the url (file/folder) to local path
        @param url - url to get file/folder from
        @param path - path to place fetched files
        '''
        print("Getting:",url,"to",dest)
        return False
    def close(self):
        '''
        Close this connection
        '''
        print("Closing backend")
    def rm(self,url):
        '''
        Remove this file/folder
        '''
        print("Removing product at:",url)
        return False
