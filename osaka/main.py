import osaka.base
import osaka.utils
import osaka.transfer

def put(path,url,params={},measure=False,output="./pge_metrics.json",lockMetadata={},retries=0, ncoop=False, noclobber=False):
    '''
    Put a file up to given url based on its scheme
    @param path: path to read file from (locally)
    @param url: url to put file at
    @param params: (optional)parameters to hand to backend, like passwords/usernames
    @param measure: (optional)take transfer metrics, True/False
    @param output: (optional)output file to place metrics in
    @param lockMetadata: (optional)metadata to place in Osaka lock-out file
    @param retries: (optional)number of times to retry
    '''
    osaka.utils.LOGGER.info("Running backwards-compatible 'Osaka Put' from {0} to {1}".format(path,url))
    transfer(path, url, params, measure, output, lockMetadata,retries=retries, ncoop=ncoop, noclobber=noclobber)
def get(url,path,params={},measure=False,output="./pge_metrics.json",lockMetadata={},retries=0,force=False, ncoop=False, noclobber=False):
    '''
    Get a URL to the given path based on scheme
    @param url: url to grab file from
    @param path: path to save file to (locally)
    @param params: (optional)parameters to hand to backend, like passwords/usernames
    @param measure: (optional)take transfer metrics, True/False
    @param output: (optional)output file to place metrics in
    @param lockMetadata: (optional)metadata to place in Osaka lock-out file
    @param retries: (optional)number of times to retry
    '''
    osaka.utils.LOGGER.info("Running backwards-compatible 'Osaka Get' from {0} to {1}".format(url,path))
    transfer(url, path, params, measure, output, lockMetadata,retries=retries,force=force, ncoop=ncoop, noclobber=noclobber)
def transfer(source,dest,params={},measure=False,output="./pge_metrics.json",lockMetadata={},retries=0,force=False, ncoop=False, noclobber=False):
    '''
    Transfer from one point to another
    @param source: source URI to transfer from
    @param dest: destination URI to transfer to
    @param params: (optional)parameters to hand to backend, like passwords/usernames
    @param measure: (optional)take transfer metrics, True/False
    @param output: (optional)output file to place metrics in
    @param lockMetadata: (optional)metadata to place in Osaka lock-out file
    @param retries: (optional)number of times to retry
    '''
    osaka.utils.LOGGER.info("Running new-style 'Osaka Transfer' from {0} to {1}".format(source,dest))
    #if source.startswith("rsync://") or dest.startswith("rsync://"):
    #    rsync(source,dest,params,measure,output,lockMetadata)
    transfer = osaka.transfer.Transferer()
    transfer.transfer(source,dest,params=params,measure=measure,metricsOutput=output,lockMetadata=lockMetadata,retries=retries,force=force,ncoop=ncoop,noclobber=noclobber)
# def rsync(source,dest,params={},measure=False,output="./pge_metrics.json",lockMetadata={}):
#     '''
#     Rsync from one backend to a valid rsync location
#     @param source: osaka-source URI to transfer from
#     @param dest: rsync destination URI to transfer to
#     @param params: (optional)parameters to hand to osaka-backend, like passwords/usernames
#     @param measure: (optional)take transfer metrics, True/False
#     @param output: (optional)output file to place metrics in
#     @param lockMetadata: (optional)metadata to place in Osaka lock-out file
#     @param retries: (optional)number of times to retry
#     '''
#     rsyncer = osaka.rsyncer.Rsyncer()
#     rsyncer.transfer(source,dest,params,measure,output,lockMetadata)
def rmall(url,params={},unlock=False,retries=0):
    '''
    Remove a URL, recursively
    @param url: url to remove
    @param params: (optional)parameters to hand to backend, like passwords/usernames
    @param retries: (optional)number of times to retry
    '''
    osaka.utils.LOGGER.info("Removing {0}".format(url))
    transfer = osaka.transfer.Transferer()
    transfer.remove(url,params,unlock=unlock,retries=retries)
def isLocked(url,params={}):
    '''
    Is the URL locked?
    @param url: url to remove
    @param params: (optional)parameters to hand to backend, like passwords/usernames
    '''
    osaka.utils.LOGGER.info("Checking lock status of {0}".format(url))
    transfer = osaka.transfer.Transferer()
    return transfer.isLocked(url,params=params)
def exists(url,params={}):
    '''
    Checks the existence of a url
    @param url: url to check
    @param params: params to pass-in 
    '''
    backend = osaka.base.StorageBase.getStorageBackend(url)
    backend.connect(url,params)
    return backend.exists(url)
def size(url, params={}, retries=0, force=False):
    '''
    Check the size of an object
    '''
    uri = url.rstrip("/")
    osaka.utils.LOGGER.info("Sizing URI {0}".format(uri))
    handle = osaka.base.StorageBase.getStorageBackend(uri)
    lock = osaka.lock.Lock(uri, handle)
    for retry in range(0,retries+1):
        try:
            handle.connect(uri,params)
            if not force and lock.isLocked():
                error = "URI {0} has not completed previous tranfer. Will not continue.".format(uri)
                osaka.utils.LOGGER.error(error)
                raise osaka.utils.OsakaException(error)
            def size_it(item):
                ''' Size one item '''
                osaka.utils.LOGGER.debug("Sizing specific item {0}".format(item))
                return handle.size(item)
            return sum(osaka.utils.product_composite_iterator(uri, handle, size_it))
        except Exception as e:
            osaka.utils.LOGGER.warning("Exception occurred, retrying({0}): {1}".format(retry+1,e))
        finally:
            handle.close()
    else:
        raise
def list(url, params={}, retries=0, force=False):
    return getChildren(url, params=params, retries=retries, force=force)
def getChildren(url, params={}, retries=0, force=False):
    '''
    Check the size of an object
    '''
    uri = url.rstrip("/")
    osaka.utils.LOGGER.info("Get all children URI {0}".format(uri))
    handle = osaka.base.StorageBase.getStorageBackend(uri)
    lock = osaka.lock.Lock(uri, handle)
    for retry in range(0,retries+1):
        try:
            handle.connect(uri,params)
            if not force and lock.isLocked():
                error = "URI {0} has not completed previous tranfer. Will not continue.".format(uri)
                osaka.utils.LOGGER.error(error)
                raise osaka.utils.OsakaException(error)
            def identity(item):
                ''' Size one item '''
                return item
            return osaka.utils.product_composite_iterator(uri, handle, identity)
        except Exception as e:
            osaka.utils.LOGGER.warning("Exception occurred, retrying({0}): {1}".format(retry+1,e))
        finally:
            handle.close()
    else:
        raise

def supported(url):
    '''
    Check to see if the url's scheme is supported
    @param url: url whose scheme to check
    '''
    osaka.utils.LOGGER.info("Checking for backend supporting {0}".format(url))
    try:
        return not osaka.base.StorageBase.getStorageBackend(url) is None
    except osaka.utils.OsakaException:
        return False
