from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import open
from builtins import int
from builtins import str
from future import standard_library

standard_library.install_aliases()
import re
import traceback
import backoff
import boto3
import botocore
import urllib.parse
import datetime
import os.path
import json
import osaka.base
import osaka.utils
import osaka.storage.file

"""
S3 storage connection service
@author starchmd,gmanipon
"""
# S3 region info
S3_REGION_INFO = None

# entry that holds the default region
DEFAULT_REGION = None

# regexes
NOT_FOUND_RE = re.compile(r"Not Found")


def get_region_info():
    """
    Return region info dict.
    """
    global S3_REGION_INFO
    global DEFAULT_REGION
    if S3_REGION_INFO is None and DEFAULT_REGION is None:
        S3_REGION_INFO = {}
        DEFAULT_REGION = ""
        s = botocore.session.get_session()
        DEFAULT_REGION = s.get_config_variable('region')
        for part in s.get_available_partitions():
            for region in s.get_available_regions("s3", part):
                s3 = s.create_client("s3", region)
                ep = urllib.parse.urlparse(s3.meta.endpoint_url).netloc
                S3_REGION_INFO[region] = ep
    return S3_REGION_INFO, DEFAULT_REGION


class S3(osaka.base.StorageBase):
    """
    Handles S3 file copies
    """

    def __init__(self):
        """
        Constructor
        """
        self.tmpfiles = []
        self.is_nominal_style = False

    def connect(self, uri, params={}):
        """
        Connects to the backend
        @param uri - s3s or s3 uri for resource
        @param params - optional, may contain: location, aws_access_key_id, aws_secret_access_key
        """
        osaka.utils.LOGGER.debug("Opening S3 handler")
        self.cache = {}
        uri = re.compile(r'^s3s?').sub("https", uri)
        parsed = urllib.parse.urlparse(uri)
        session_kwargs = {}
        kwargs = {}
        check_host = parsed.hostname if "location" not in params else params["location"]
        region_info, default_region = get_region_info()
        found_ep_and_region = False
        for region, ep in region_info.items():
            if re.search(ep, check_host):
                kwargs["endpoint_url"] = ep
                session_kwargs["region_name"] = region
                found_ep_and_region = True
                break
        # Use the default region obtained from the sessions object when the
        # region info was being gathered. This check is used to support the cases
        # when osaka receives an S3 url in the nominal pathing style.
        if not found_ep_and_region:
            kwargs["endpoint_url"] = f"{parsed.scheme}://s3.{default_region}.amazonaws.com"
            session_kwargs["region_name"] = default_region
            self.is_nominal_style = True
        else:
            if parsed.hostname is not None:
                kwargs["endpoint_url"] = "%s://%s" % (parsed.scheme, parsed.hostname)
            else:
                kwargs["endpoint_url"] = "%s://%s" % (parsed.scheme, kwargs["endpoint_url"])
        if parsed.port is not None and parsed.port != 80 and parsed.port != 443:
            kwargs["endpoint_url"] = "%s:%s" % (kwargs["endpoint_url"], parsed.port)
        if parsed.username is not None:
            session_kwargs["aws_access_key_id"] = parsed.username
        elif "aws_access_key_id" in params:
            session_kwargs["aws_access_key_id"] = params["aws_access_key_id"]
        if parsed.password is not None:
            session_kwargs["aws_secret_access_key"] = parsed.password
        elif "aws_secret_access_key" in params:
            session_kwargs["aws_secret_access_key"] = params["aws_secret_access_key"]
        if "profile_name" in params:
            session_kwargs["profile_name"] = params["profile_name"]
        kwargs["use_ssl"] = parsed.scheme == "https"
        self.encrypt = params.get("encrypt", {}).get("type", None)
        try:
            osaka.utils.LOGGER.info(
                "Making session with: {0}".format(json.dumps(session_kwargs))
            )
            self.session = boto3.session.Session(**session_kwargs)
        except botocore.exceptions.ProfileNotFound:
            osaka.utils.LOGGER.info(
                "Profile not found. Making session with: {0}".format(
                    json.dumps(session_kwargs)
                )
            )
            del session_kwargs["profile_name"]
            self.session = boto3.session.Session(**session_kwargs)
        self.s3 = self.session.resource("s3", **kwargs)
        if self.s3 is None:
            raise osaka.utils.OsakaException("Failed to connect to S3")

    @staticmethod
    def getSchemes():
        """
        Returns a list of schemes this handler handles
        Note: handling the scheme of another handler produces unknown results
        @returns list of handled schemes
        """
        return ["s3", "s3s"]

    @backoff.on_exception(
        backoff.expo, Exception, factor=4, max_time=32, jitter=backoff.random_jitter
    )
    def reload_obj(self, obj):
        """
        Backoff-wrapped call to the boto3 S3 `Object.load()` method to mitigate
        encountered errors due to S3's eventual consistency model.
        @param obj: boto3 S3 Object object
        """
        obj.load()

    def get(self, uri):
        """
        Gets the URI (s3 or s3s) as a steam
        @param uri: uri to get
        """
        osaka.utils.LOGGER.debug("Getting stream from URI: {0}".format(uri))
        container, key = osaka.utils.get_s3_container_and_path(uri, is_nominal_style=self.is_nominal_style)
        bucket = self.bucket(container, create=False)
        obj = bucket.Object(key)
        fname = "/tmp/osaka-s3-" + str(datetime.datetime.now())
        with open(fname, "w"):
            pass
        fh = open(fname, "r+b")
        self.tmpfiles.append(fh)
        try:
            obj.download_fileobj(fh)
        except botocore.exceptions.ClientError as e:
            if NOT_FOUND_RE.search(str(e)):
                raise osaka.utils.OsakaFileNotFound(
                    "File {} doesn't exist.".format(uri)
                )
            else:
                raise
        fh.seek(0)
        return fh  # obj.get()["Body"]

    def put(self, stream, uri):
        """
        Puts a stream to a URI as a steam
        @param stream: stream to upload
        @param uri: uri to put
        """
        osaka.utils.LOGGER.debug("Putting stream to URI: {0}".format(uri))
        container, key = osaka.utils.get_s3_container_and_path(uri, is_nominal_style=self.is_nominal_style)
        bucket = self.bucket(container)
        obj = bucket.Object(key)
        extra = {}
        if self.encrypt is not None:
            extra = {"ServerSideEncryption": self.encrypt}
        with osaka.storage.file.FileHandlerConversion(stream) as fn:
            obj.upload_file(fn, ExtraArgs=extra)
        try:
            self.reload_obj(obj)
            return obj.content_length
        except:
            osaka.utils.LOGGER.warn(
                "Exponential backoff on getting content length for {} failed. {}.".format(
                    uri, traceback.format_exc()
                )
            )
            osaka.utils.LOGGER.warn("Trying alternate method.")
            return self.size(uri)

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
        container, key = osaka.utils.get_s3_container_and_path(uri, is_nominal_style=self.is_nominal_style)
        bucket = self.bucket(container, create=False)
        collection = bucket.objects.filter(Prefix=key)
        if self.is_nominal_style:
            # Needs only 1 slash because the 2nd one gets added when the "full"
            # value gets put together
            uriBase = f"{parsed.scheme}:/"
        else:
            uriBase = (
                parsed.scheme
                + "://"
                + parsed.hostname
                + (":" + str(parsed.port) if parsed.port is not None else "")
            )
        # Setup cache, and fill it with listings
        self.cache["__top__"] = uri
        for item in collection:
            if not (item.key == key or item.key.startswith(key + "/") or key == ""):
                continue
            full = uriBase + "/" + item.bucket_name + "/" + item.key
            self.cache[full] = item
            ret.append(full)
        return ret

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
        osaka.utils.LOGGER.debug("Closing S3 handler")
        for fh in self.tmpfiles:
            try:
                fh.close()
            except:
                osaka.utils.LOGGER.debug(
                    "Failed to close temporary file-handle for: {0}".format(fh.name)
                )
            try:
                os.remove(fh.name)
            except:
                osaka.utils.LOGGER.debug(
                    "Failed to remove temporary file-handle for: {0}".format(fh.name)
                )

    def size(self, uri):
        """
        Size this uri from backend
        @param uri: uri to size
        """
        if uri in self.cache:
            return self.cache[uri].size
        container, key = osaka.utils.get_container_and_path(
            urllib.parse.urlparse(uri).path
        )
        bucket = self.bucket(container, create=False)
        obj = bucket.Object(key)
        try:
            return obj.content_length
        except Exception as exc:
            if "Invalid length for parameter Key, value: 0" in str(exc):
                return 0
            raise

    def rm(self, uri):
        """
        Remove this uri from backend
        @param uri: uri to remove
        """
        container, key = osaka.utils.get_s3_container_and_path(uri, is_nominal_style=self.is_nominal_style)
        bucket = self.bucket(container, create=False)
        obj = bucket.Object(key)
        obj.delete()

    def getKeysWithPrefixURI(self, uri):
        """
        Keys with prefix of given URI
        @param uri: prefix URI
        """
        parsed = urllib.parse.urlparse(uri)
        container, key = osaka.utils.get_container_and_path(parsed.path)
        bucket = self.bucket(container, create=False)
        collection = bucket.objects.filter(Prefix=key)
        return [item.bucket_name + "/" + item.key for item in collection]

    def bucket(self, bucket, create=True):
        """
        Gets the given bucket or makes it
        @param bucket - name of bucket to find
        """
        b = self.s3.Bucket(bucket)
        exists = True
        try:
            osaka.utils.boto_wrapper(self.s3.meta.client.head_bucket, Bucket=bucket)
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 404:
                exists = False
        if exists is False and create:
            loc = re.sub(r"s3.([^.]+)\..*", r"\g<1>", self.s3.host)
            if loc == "amazonaws":
                loc = ""  # handle us-east-1
            b = osaka.utils.boto_wrapper(self.s3.create_bucket,
                Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": loc}
            )
        return b
