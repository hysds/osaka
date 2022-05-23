from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from builtins import int
from builtins import map
from builtins import str
from future import standard_library

standard_library.install_aliases()
import logging
import subprocess
import urllib.parse
import backoff
import botocore.exceptions

LOGGER = logging.getLogger("osaka")

DU_CALC = {"GB": 1024 ** 3, "MB": 1024 ** 2, "KB": 1024}


def get_uri_username_and_password(uri):
    """
    Parses the URI and returns the username and password
    @param uri: URI for the end point
    @return: tuple containing the username/password from the URI 
    """
    temp = urllib.parse.urlparse(uri)
    return (temp.username, temp.password)


def get_uri_scheme_and_hostname(uri):
    """
    Parses the URI and returns the scheme and hostname
    @param uri: URI for the end point
    @return: tuple containing the scheme/hostname from the URI 
    """
    temp = urllib.parse.urlparse(uri)
    host = temp.hostname + ("" if temp.port is None else ":" + str(temp.port))
    return (temp.scheme, host)


def get_uri_path(uri):
    """
    Gets the path from the uri
    @param uri: uri from which to parse path
    @return: path portion of URI
    """
    temp = urllib.parse.urlparse(uri)
    return temp.path


def get_container_and_path(urlpath):
    """
    Gets the container and path from the given url
    @param urlpath - url's path to determine container and path from
    """
    split = urlpath.lstrip("/").split("/", 1)
    return (split[0], "" if not len(split) > 1 else split[1])


def get_s3_container_and_path(s3_url, is_nominal_style=False):
    """
    Gets the s3 container (a.k.a. bucket) and path (a.k.a key) from the
    given url.

    :param s3_url: The S3 url to parse.
    :param is_nominal_style: Set to true if the given S3 url is in a
    nominal style format (i.e. s3://bucket/key). Otherwise, set to false.
    :return:
    """
    parsed = urllib.parse.urlparse(s3_url)
    if is_nominal_style is True:
        # If we are dealing with the nominal S3 style path
        return parsed.hostname, parsed.path.split("/", 1)[1]
    else:
        return get_container_and_path(parsed.path)


# def walk(func, directory,destdir, *params):
#    '''
#    Walk the directory and call the function for each file
#    @param func - function to call back
#    @param directory - directory to walk
#    @param params - params to pass through
#    '''
#    ret = True
#    for dir,unused,files in os.walk(directory):
#        for file in files:
#            full = os.path.join(dir,file)
#            dest = os.path.join(destdir,os.path.relpath(full,directory))
#            ret = ret and func(full,dest,*params)
#    return ret


def get_disk_usage(path):
    """Return disk size, "du -sk", for a path."""
    return int(subprocess.check_output(["du", "-sk", path]).split()[0]) * DU_CALC["KB"]


def human_size(size):
    """Return the human size"""
    for tmp in ["GB", "MB", "KB"]:
        if size > DU_CALC[tmp]:
            return (size / float(DU_CALC[tmp]), tmp)
    return (size, "B")


def product_composite_iterator(base, handle, callback, include_top=False):
    """
    A function to walk through an osaka product enabling handling of
    coposite childeren. Note: if not a composite product, nothing happens.
    @param base: base of the product
    @param handle: handler for the backend
    @param callback: callback taking uri, and relative path
    @param include_top: include top of composite
    """
    uris = [base]
    if handle.isComposite(base):
        uris = handle.listAllChildren(base)
        if include_top:
            uris.append(base)
    return list(map(callback, uris))


@backoff.on_exception(
    backoff.expo, botocore.exceptions.NoCredentialsError, factor=4, max_time=32, jitter=backoff.random_jitter
)
def boto_wrapper(f, *args, **kargs):
    return f(*args, **kargs)


class OsakaException(Exception):
    pass


class CooperationNotPossibleException(OsakaException):
    pass


class CooperationRefusedException(OsakaException):
    pass


class TimeoutException(OsakaException):
    pass


class NoClobberException(OsakaException):
    pass


class OsakaFileNotFound(OsakaException):
    pass
