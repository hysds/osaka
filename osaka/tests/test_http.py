import unittest
import osaka.storage.http
import requests

from unittest.mock import patch, Mock


class StorageHTTPTest(unittest.TestCase):
    def test_isComposite_with_binary_file(self):
        test_url = "https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/images/kilauea17_0.png"

        storage_http = osaka.storage.http.HTTP()
        try:
            storage_http.connect(test_url)
            self.assertFalse(storage_http.isComposite(test_url))
        finally:
            storage_http.close()

    def test_200_http_status(self):
        test_url = "https://example.com"
        storage_http = osaka.storage.http.HTTP()
        storage_http.connect(test_url)
        storage_http.get(test_url)
        storage_http.close()

    @patch('osaka.storage.http.requests.Session.get')
    def test_202_http_status(self, mock_get):
        # Mock a 202 response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        mock_get.return_value = mock_response

        test_url = "https://httpstat.us/202"
        storage_http = osaka.storage.http.HTTP()
        storage_http.connect(test_url)
        self.assertRaises(
            osaka.storage.http.HTTPStatusCode200Exception, storage_http.get, test_url
        )
        storage_http.close()

    def test_404_http_status(self):
        test_url = "https://example.com/nonexistent"
        storage_http = osaka.storage.http.HTTP()
        storage_http.connect(test_url)
        self.assertRaisesRegex(
            osaka.utils.OsakaFileNotFound,
            "File {} doesn't exist.".format(test_url),
            storage_http.get,
            test_url,
        )
        storage_http.close()
