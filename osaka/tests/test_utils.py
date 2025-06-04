import unittest

from osaka import utils


class UtilsTest(unittest.TestCase):
    def setUp(self):
        self.legacy_s3_url = "s3://s3-us-west-2.amazonaws.com:80/my_bucket/foo/bar/key"
        self.nominal_s3_url = "s3://my_bucket/foo/bar/key"
        self.expected_container = "my_bucket"
        self.expected_key = "foo/bar/key"

    def test_get_s3_container_and_path_legacy_style(self):
        container, key = utils.get_s3_container_and_path(self.legacy_s3_url)
        self.assertEqual(container,
                          self.expected_container,
                          f"Did not get expected container value: "
                          f"container={container}, expected={self.expected_container}")
        self.assertEqual(key, self.expected_key, f"Did not get expected key value: key={key}, "
                                              f"expected={self.expected_key}")

    def test_get_s3_container_and_path_nominal_style(self):
        container, key = utils.get_s3_container_and_path(self.nominal_s3_url, is_nominal_style=True)
        self.assertEqual(container, self.expected_container,
                          f"Did not get expected container value: "
                          f"container={container}, expected={self.expected_container}")
        self.assertEqual(key, self.expected_key, f"Did not get expected key value: key={key}, "
                                              f"expected={self.expected_key}")


if __name__ == "__main__":
    unittest.main()
