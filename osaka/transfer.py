'''
Created on Apr 27, 2016

@author: mstarch
'''
import os
import json
import socket
import datetime

#Osaka imports
import osaka.base
import osaka.lock
import osaka.cooperator
import osaka.utils

class Transferer(object):
    '''
    A class used to atomically transfer files between Osaka storage endpoints
    '''
    def transfer(self,source,dest,params={},measure=False,metricsOutput="./pge_metrics.json",lockMetadata={},retries=0,force=False,ncoop=False,noclobber=False):
        '''
        Transfer an objects between source and dest
        @param source: source osaka-style URI
        @param dest: destination osaka-style URI
        @param lockMetadata: (optional) extra metadata for adding to lock file
        @param retries: (optional) number of times to retry a command
        @param force: force a fetch of failed transfers
        @param ncoop: fail rather than cooperate with an already running osaka
        @param noclobber: raise exception if you will clobber an existing object
        '''
        metrics = None
        #Refine uris to be standard
        source = source.rstrip("/")
        dest = dest.rstrip("/")
        osaka.utils.LOGGER.info("Opening connections for {0} and {1}".format(source,dest))
        #Get handlers for the source and destination
        shandle = osaka.base.StorageBase.getStorageBackend(source)
        dhandle = osaka.base.StorageBase.getStorageBackend(dest)
        for retry in range(0,retries+1):
            try:
                shandle.connect(source,params)
                dhandle.connect(dest,params)
                #Check if destination is a waiting directory
                if dhandle.exists(dest) and dhandle.isComposite(dest):
                    dest = os.path.join(dest,os.path.basename(source))
                slock = osaka.lock.Lock(source, shandle)
                dlock = osaka.lock.Lock(dest, dhandle)
                if source == dest:
                    error = "Source, {0}, and destination, {1}, are the same".format(source,dest)
                    osaka.utils.LOGGER.error(error)
                    raise osaka.utils.OsakaException(error)
                elif dhandle.exists(dest) and noclobber:
                    error = "Destination, {0}, already exists and no-clobber is set".format(dest)
                    osaka.utils.LOGGER.error(error)
                    raise osaka.utils.NoClobberException(error)
                if slock.isLocked() and not force:
                    error = "Source {0} has not completed previous tranfer. Will not continue.".format(source)
                    osaka.utils.LOGGER.error(error)
                    raise osaka.utils.OsakaException(error)
                elif slock.isLocked() and force:
                    error = "Source {0} has not completed previous tranfer. Will continue by force.".format(source)
                    osaka.utils.LOGGER.warning(error)
                osaka.utils.LOGGER.info("Transferring between {0} and {1}".format(source,dest))
                #Atomically upload the file or files
                with osaka.cooperator.Cooperator(source, dlock, lockMetadata) as coop:
                    if coop.isPrimary():
                        metrics = self.transfer_uri(source, shandle, dest, dhandle)
                    elif ncoop:
                        raise osaka.utils.CooperationRefusedException("Competeing Osaka instance running, and cooperation was turned off")
                    else:
                        osaka.cooperator.Spinner(dlock, params.get("timeout", -1)).spin()
                break
            except Exception as e:
                osaka.utils.LOGGER.warning("Exception occurred, retrying({0}): {1}".format(retry+1,e))
            finally:
                shandle.close()
                dhandle.close()
        #If we never reach the break, reraise the last exception that happened
        else:
            raise
        if measure and not metrics is None:
            self.writeMetrics(metrics,metricsOutput)
    def transfer_uri(self, source, shandle, dest, dhandle):
        '''
        Transfer a URI recursing into it if it is a composite
        '''
        metrics = {
            "source":source,
            "destination":dest,
            "type":"osaka-transfer",
            "time_start":datetime.datetime.utcnow()
        }
        def transfer_one(uri):
            ''' Transfer a single item '''
            relative = os.path.relpath(uri,source)
            specificDest = dest if relative == "." else os.path.join(dest,relative)
            osaka.utils.LOGGER.debug("Transferring individual object from {0} to {1}".format(uri,specificDest))
            stream = shandle.get(uri)
            count = dhandle.put(stream,specificDest)
            stream.close()
            return count
        counts = osaka.utils.product_composite_iterator(source, shandle, transfer_one)
        metrics["time_end"] = datetime.datetime.utcnow()
        metrics["size"] = sum(counts)
        return metrics
    def remove(self,uri,params={},unlock=False,retries=0):
        '''
        Removal URI and all children
        @param uri: URI to remove
        @param unlock: shall we unlock first? Otherwise error on locked file
        '''
        uri = uri.rstrip("/")
        osaka.utils.LOGGER.info("Removing URI {0}".format(uri))
        handle = osaka.base.StorageBase.getStorageBackend(uri)
        lock = osaka.lock.Lock(uri, handle)
        for retry in range(0,retries+1):
            try:
                handle.connect(uri,params)
                if not unlock and lock.isLocked():
                    error = "URI {0} has not completed previous tranfer. Will not continue.".format(uri)
                    osaka.utils.LOGGER.error(error)
                    raise osaka.utils.OsakaException(error)
                elif lock.isLocked():
                    lock.unlock()
                def remove_one(item):
                    ''' Remove one item '''
                    osaka.utils.LOGGER.debug("Removing specific item {0}".format(item))
                    handle.rm(item)
                osaka.utils.product_composite_iterator(uri, handle, remove_one, 
                                                       False if handle.isObjectStore() else True)
                break
            except Exception as e:
                osaka.utils.LOGGER.warning("Exception occurred, retrying({0}): {1}".format(retry+1,e))
            finally:
                handle.close()
        else:
            raise
    def writeMetrics(self,metrics,output):
        '''
        Write out all the metrics
        @param metrics - metrics collected
        @param output - output file
        '''
        osaka.utils.LOGGER.info("Attempting to merge metrics with: {0}".format(output))
        #Rectify metrics
        metrics["duration"] = (metrics["time_end"] - metrics["time_start"]).total_seconds()
        metrics["transfer_rate"] = metrics["size"]/metrics["duration"]
        metrics["time_start"] = metrics["time_start"].isoformat()+"Z"
        metrics["time_end"] = metrics["time_end"].isoformat()+"Z"
        try:
            #Read input data
            data = {}
            if os.path.exists(output):
                osaka.utils.LOGGER.info("Loaded metadata from: {0}".format(output))
                with open(output,"r") as inputf:
                    data = json.load(inputf)
            #Add metric
            data.setdefault(metrics['type'], []).append(metrics)
            #Write out the file
            osaka.utils.LOGGER.info("Writing metric to: {0}".format(output))
            with open(output,"w") as outputf:
                json.dump(data, outputf)
        except Exception as e:
            osaka.utils.LOGGER.warning("Error merging metrics with: {0} Error: {1}".format(output,str(e)))
            raise e
            
