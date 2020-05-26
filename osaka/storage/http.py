from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from builtins import int
from builtins import next
from builtins import str
from future import standard_library

standard_library.install_aliases()
import os
import re
import urllib.parse
import requests

from requests.auth import HTTPBasicAuth, HTTPDigestAuth

import osaka.utils
import osaka.base

requests.packages.urllib3.disable_warnings()
"""
HTTP Handler

This Osaka backend uses requests to handle HTTP requests. 

@author starchmd
"""


class HTTPStatusCode200Exception(Exception):
    """Exception class for 202 HTTP status code."""


class HTTP(osaka.base.StorageBase):
    """
    Http and WebDav handling backends
    """

    BLOCK_SIZE = 4096
    HREF_RE = re.compile(r'href\s*=\s*"([^"]+)"')

    def __init__(self):
        """
        Constructor
        """

    def connect(self, uri, params={}):
        """
        Connects to the backend
        """
        self.timeout = 1800.0 if "timeout" not in params else params["timeout"]
        parsed = urllib.parse.urlparse(uri)
        user = None if "user" not in parsed else parsed["user"]
        password = None if "password" not in parsed else parsed["password"]
        osaka.utils.LOGGER.debug("Opening HTTP handler")
        if user is None or password is None:
            tmp = self.getNetRCCredentials(uri)
            user = None if tmp is None else tmp["user"]
            password = None if tmp is None else tmp["password"]
        if "oauth" in params and not params["oauth"] is None:
            osaka.utils.LOGGER.info(
                "Connecting to http using OAuth: {0}".format(params["oauth"])
            )
            self.session = self.oauthSession(params["oauth"])
        else:
            # connectionUri = parsed.scheme + "://" +parsed.hostname+(":"+str(parsed.port) if not parsed.port is None else "")
            osaka.utils.LOGGER.info(
                "Connecting to http using with http: {0} with user: {1} and password {2}".format(
                    uri, user, password
                )
            )
            self.session = self.standardSession(uri, user, password, self.timeout)

    @staticmethod
    def getSchemes():
        """
        Returns a list of schemes this handler handles
        Note: handling the scheme of another handler produces unknown results
        @returns list of handled schemes
        """
        return ["http", "https"]

    def get(self, uri, text=False):
        """
        Gets the URI (file) as a steam
        @param uri: uri to get
        @param text: should we pull out text data instead of raw
        """
        osaka.utils.LOGGER.debug(
            "Getting stream from URI: {0} Timeout: {1}".format(uri, self.timeout)
        )
        response = self.session.get(
            uri, stream=True, verify=False, timeout=self.timeout
        )
        osaka.utils.LOGGER.debug(
            "Got HTTP status code: {}".format(response.status_code)
        )
        response.raise_for_status()

        # catch 202 status code
        if response.status_code == 202:
            raise HTTPStatusCode200Exception(
                "Received 202 HTTP status code: {}".format(response.text)
            )

        if text:
            return response.text
        return response.raw

    def put(self, stream, uri):
        """
        Puts a stream to a URI as a steam
        @param stream: stream to upload
        @param uri: uri to put
        """
        raise osaka.utils.OsakaException("Osaka HTTP does not support PUT requests")

    def size(self, uri):
        """
        Get size try
        @param uri: uri to check
        """
        osaka.utils.LOGGER.debug(
            "Getting size of {0} exist? Timeout: {1}".format(uri, self.timeout)
        )
        response = self.session.get(
            uri, stream=True, verify=False, timeout=self.timeout
        )
        response.raise_for_status()
        size = int(response.headers["content-length"])
        response.close()
        return size

    def exists(self, uri):
        """
        Does the URI exist?
        @param uri: uri to check
        """
        osaka.utils.LOGGER.debug(
            "Does URI {0} exist? Timeout: {1}".format(uri, self.timeout)
        )
        try:
            ret = self.session.head(uri, timeout=self.timeout)
            # Custom raise_for_status, to include any non-200 code forcing a different check
            if ret.status_code != 200:
                raise osaka.utils.OsakaException("Bad response for existence checking")
            return True
        except Exception:
            pass
        osaka.utils.LOGGER.debug("HEAD call not allowed, attempting get w/o read")
        try:
            text = self.get(uri, text=True)
            if re.search(r"\s*(?:<!DOCTYPE)|(?:<!doctype)", text):
                raise osaka.utils.OsakaException("Unauthorized, redirected to login")
            osaka.utils.LOGGER.debug("Does URI {0} exist? {1}".format(uri, True))
            return True
        except Exception as e:
            if "404 Client Error:" in str(e):
                osaka.utils.LOGGER.debug("Does URI {0} exist? {1}".format(uri, False))
                return False
            raise

    def list(self, uri):
        """
        List URI
        @param uri: uri to list
        """
        osaka.utils.LOGGER.debug(
            "Listing {0} composite. Timeout: {1}".format(uri, self.timeout)
        )
        response = self.session.get(
            uri, stream=True, verify=False, timeout=self.timeout
        )
        response.raise_for_status()
        chunks = response.iter_content(chunk_size=self.BLOCK_SIZE)
        try:
            first = next(chunks)
        except StopIteration:
            first = ""
        if first.startswith(
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"'
        ):
            for chunk in chunks:
                first += chunk
            return [os.path.join(uri, child) for child in self.harvestChildren(first)]

    def isComposite(self, uri):
        """
        Detect if this uri is a composite uri (uri to collection of objects i.e. directory)
        @param uri: uri to list
        """
        osaka.utils.LOGGER.debug(
            "Is URI {0} composite? Timeout: {1}".format(uri, self.timeout)
        )
        response = self.session.get(
            uri, stream=True, verify=False, timeout=self.timeout
        )
        response.raise_for_status()
        chunks = response.iter_content(chunk_size=self.BLOCK_SIZE)
        try:
            first = next(chunks)
        except StopIteration:
            first = ""
        response.close()
        if isinstance(first, str) and first.startswith(
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"'
        ):
            osaka.utils.LOGGER.debug("Is URI {0} composite? {1}".format(uri, True))
            return True
        elif isinstance(first, bytes) and first.startswith(
            b'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"'
        ):
            osaka.utils.LOGGER.debug("Is URI {0} composite? {1}".format(uri, True))
            return True
        osaka.utils.LOGGER.debug("Is URI {0} composite? {1}".format(uri, False))
        return False

    def isObjectStore(self):
        return False

    def close(self):
        """
        Close this backend
        """
        osaka.utils.LOGGER.debug("Closing file handler")
        if self.session is not None:
            self.session.close()

    def rm(self, uri):
        """
        Remove this uri from backend
        @param uri: uri to remove
        """
        raise osaka.utils.OsakaException("Osaka HTTP does not support 'rm' requests")

    @classmethod
    def getNetRCCredentials(clazz, url):
        """
        Look up .netrc params 
        @param url - url to lookup .netrc parameters for
        """
        creds = requests.utils.get_netrc_auth(url)
        if creds is None:
            return None
        user, password = creds
        # Grab credentials, using site-specific names or default to "user" and "password
        creds = {}
        key = "user"
        val = user
        if ":" in user:
            key, val = user.split(":", 1)
        creds[key] = val
        key = "password"
        val = password
        if ":" in password:
            key, val = password.split(":", 1)
        creds[key] = val
        return creds

    @classmethod
    def standardSession(clazz, uri, user, password, timeout=1800.0):
        """
        Gets a standard requests session
        @param uri - uri to authentigate against
        @param user - username to use, may be None
        @param password - password to connect with, may be None
        @return: requests session
        """
        # try:
        creds = clazz.getNetRCCredentials(uri)
        if user is not None and password is not None:
            creds = {"user": user, "password": password}
        session = requests.Session()
        if creds is None:
            return session
        session.auth = HTTPBasicAuth(creds["user"], creds["password"])
        # Attempt a connection, if fail change url
        response = session.get(uri, stream=True, verify=False, timeout=timeout)
        if response.status_code == 401:
            session.auth = HTTPDigestAuth(creds["user"], creds["password"])
        return session
        # except Exception as e:
        #    raise osaka.utils.OsakaException("Failed to get standard session: {0}".format(e))

    @classmethod
    def oauthSession(clazz, oauth):
        """
        Returns an oauth session for use with this backend.
        @param oauth - oauth url to connect to
        @return: oauth session
        """
        try:
            creds = clazz.getNetRCCredentials(oauth)
            if creds is None:
                raise osaka.utils.OsakaException(
                    "Failed to get OAuth credentials from .netrc"
                )
            session = requests.Session()
            session.post(oauth, params=creds, verify=False).raise_for_status()
        except Exception as e:
            raise osaka.utils.OsakaException(
                "Failed to get OAuth session from: {0}. {1}".format(oauth, e)
            )
        return session

    @classmethod
    def harvestChildren(clazz, blob):
        """
        Harvests child links from the HTML that is returned from webdav
        @param blob - blob of text which is the HTML page
        """
        children = set()
        for match in clazz.HREF_RE.finditer(blob):
            child = match.group(1)
            if (
                not child.startswith("?")
                and not child.startswith("/")
                and not child.startswith("..")
                and not child.startswith("https://")
                and not child.startswith("#")
                and not child.startswith("'")
                and not child.startswith("http://")
            ):
                children.add(child)
        return children
