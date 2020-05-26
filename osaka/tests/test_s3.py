import io
import unittest
from mock import patch
from moto import mock_s3
import botocore
from botocore.exceptions import ClientError
import boto3

import osaka.storage.s3


orig = botocore.client.BaseClient._make_api_call

mock_counter = 0
mock_counter_threshold = 3


def mock_make_api_call(self, operation_name, kwarg):
    """Mock the HeadObject operation to raise a 404."""

    if operation_name == "HeadObject":
        parsed_response = {"Error": {"Code": "404", "Message": "Not Found"}}
        raise ClientError(parsed_response, operation_name)
    return orig(self, operation_name, kwarg)


def counted_mock_make_api_call(self, operation_name, kwarg):
    """Mock the HeadObject operation to raise a 404 until a counter is reached."""

    global mock_counter
    mock_counter += 1
    if operation_name == "HeadObject" and mock_counter < mock_counter_threshold:
        parsed_response = {"Error": {"Code": "404", "Message": "Not Found"}}
        raise ClientError(parsed_response, operation_name)
    return orig(self, operation_name, kwarg)


class StorageS3Test(unittest.TestCase):
    @mock_s3
    def setUp(self):
        """Setup."""

        self.test_url = "s3://s3.us-west-2.amazonaws.com/landsat-pds/scene_list.gz"
        self.s3 = boto3.client("s3", region_name="us-west-2")

    @mock_s3
    def test_s3_get(self):
        """Test get from S3."""

        self.s3.create_bucket(
            Bucket="landsat-pds",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )
        self.s3.put_object(
            Bucket="landsat-pds", Key="scene_list.gz", Body="test_s3_get"
        )
        storage_s3 = osaka.storage.s3.S3()
        storage_s3.connect(self.test_url)
        fh = storage_s3.get(self.test_url)
        assert fh.read().decode() == "test_s3_get"
        storage_s3.close()

    @mock_s3
    def test_s3_put(self):
        """Test put to S3."""

        self.s3.create_bucket(
            Bucket="landsat-pds",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )
        storage_s3 = osaka.storage.s3.S3()
        storage_s3.connect(self.test_url)
        f = io.StringIO("test_s3_put")
        storage_s3.put(f, self.test_url)
        storage_s3.close()
        obj = self.s3.get_object(Bucket="landsat-pds", Key="scene_list.gz")
        assert obj["Body"].read().decode() == "test_s3_put"

    @mock_s3
    def test_s3_eventual_consistency_error(self):
        """Test exponential backoff works to retry object
           metadata reload for some time and eventually bubbles up the exception."""

        self.s3.create_bucket(
            Bucket="landsat-pds",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )
        with self.assertRaises(ClientError):
            with patch(
                "botocore.client.BaseClient._make_api_call", new=mock_make_api_call
            ):
                storage_s3 = osaka.storage.s3.S3()
                storage_s3.connect(self.test_url)
                f = io.StringIO("test_s3_eventual_consistency_error")
                storage_s3.put(f, self.test_url)

    @mock_s3
    def test_s3_eventual_consistency_handling(self):
        """Test exponential backoff works to retry object metadata reload for some time and 
           eventually succeeds."""

        self.s3.create_bucket(
            Bucket="landsat-pds",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )
        with patch(
            "botocore.client.BaseClient._make_api_call", new=counted_mock_make_api_call
        ):
            storage_s3 = osaka.storage.s3.S3()
            storage_s3.connect(self.test_url)
            f = io.StringIO("test_s3_eventual_consistency_handling")
            storage_s3.put(f, self.test_url)
            storage_s3.close()
            obj = self.s3.get_object(Bucket="landsat-pds", Key="scene_list.gz")
            assert (
                obj["Body"].read().decode() == "test_s3_eventual_consistency_handling"
            )
