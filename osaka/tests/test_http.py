import unittest
import requests.exceptions

import osaka.storage.http


class StorageHTTPTest(unittest.TestCase):

    def test_isComposite_with_binary_file(self):
        test_url = "http://landsat-pds.s3.amazonaws.com/scene_list.gz"

        storage_http = osaka.storage.http.HTTP()
        try:
            storage_http.connect(test_url)
            self.assertFalse(storage_http.isComposite(test_url))
        finally:
            storage_http.close()

    def test_200_http_status(self):
        test_url = "https://httpstat.us/200"
        storage_http = osaka.storage.http.HTTP()
        storage_http.connect(test_url)
        storage_http.get(test_url)
        storage_http.close()

    def test_202_http_status(self):
        test_url = "https://httpstat.us/202"
        storage_http = osaka.storage.http.HTTP()
        storage_http.connect(test_url)
        self.assertRaises(osaka.storage.http.HTTPStatusCode200Exception,
                          storage_http.get, test_url)
        storage_http.close()

    def test_404_http_status(self):
        test_url = "https://httpstat.us/404"
        storage_http = osaka.storage.http.HTTP()
        storage_http.connect(test_url)
        self.assertRaisesRegex(requests.exceptions.HTTPError, 
                               "404 Client Error.+$",
                               storage_http.get, test_url)
        storage_http.close()
