import unittest

from osaka import utils


class UtilsTest(unittest.TestCase):
    def setUp(self):
        self.legacy_s3_url = "s3://s3-us-west-2.amazonaws.com:80/nisar-dev-rs-fwd-mcayanan/products/NEN_L_RRST/" \
                             "2020/008/NISAR_S198_ASF_AS4_M00_P00114_R00_C00_G00_2020_008_08_00_00_000000000.vc24"
        self.nominal_s3_url = "s3://nisar-dev-rs-fwd-mcayanan/products/NEN_L_RRST/" \
                              "2020/008/NISAR_S198_ASF_AS4_M00_P00114_R00_C00_G00_2020_008_08_00_00_000000000.vc24"
        self.expected_container = "nisar-dev-rs-fwd-mcayanan"
        self.expected_key = "products/NEN_L_RRST/2020/008/" \
                            "NISAR_S198_ASF_AS4_M00_P00114_R00_C00_G00_2020_008_08_00_00_000000000.vc24"

    def test_get_s3_container_and_path_legacy_style(self):
        container, key = utils.get_s3_container_and_path(self.legacy_s3_url)
        self.assertEquals(container,
                          self.expected_container,
                          f"Did not get expected container value: "
                          f"container={container}, expected={self.expected_container}")
        self.assertEquals(key, self.expected_key, f"Did not get expected key value: key={key}, "
                                                  f"expected={self.expected_key}")

    def test_get_s3_container_and_path_nominal_style(self):
        container, key = utils.get_s3_container_and_path(self.nominal_s3_url, is_nominal_style=True)
        self.assertEquals(container, self.expected_container,
                          f"Did not get expected container value: "
                          f"container={container}, expected={self.expected_container}")
        self.assertEquals(key, self.expected_key, f"Did not get expected key value: key={key}, "
                                                  f"expected={self.expected_key}")


if __name__ == "__main__":
    unittest.main()
