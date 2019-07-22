import unittest

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
