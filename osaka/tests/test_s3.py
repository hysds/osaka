import io
import unittest
from mock import patch
from moto import mock_aws
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
    @mock_aws
    def setUp(self):
        """Setup."""

        self.test_url = "s3://s3.us-west-2.amazonaws.com/landsat-pds/scene_list.gz"
        self.s3 = boto3.client("s3", region_name="us-west-2")

    @mock_aws
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

    @mock_aws
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

    @mock_aws
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

    @mock_aws
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

    @mock_aws
    def test_s3_cross_region_bucket_access(self):
        """Test that osaka can detect and handle buckets in different regions."""

        # Create buckets in different regions
        s3_west = boto3.client("s3", region_name="us-west-2")
        s3_west.create_bucket(
            Bucket="west-bucket",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )
        s3_west.put_object(
            Bucket="west-bucket", Key="test.txt", Body="west data"
        )

        s3_east = boto3.client("s3", region_name="us-east-1")
        s3_east.create_bucket(Bucket="east-bucket")
        s3_east.put_object(
            Bucket="east-bucket", Key="test.txt", Body="east data"
        )

        # Test accessing west bucket with nominal-style URL
        storage_s3 = osaka.storage.s3.S3()
        west_url = "s3://west-bucket/test.txt"
        storage_s3.connect(west_url, params={"aws_access_key_id": "test", "aws_secret_access_key": "test"})

        # Verify region cache is populated
        assert "west-bucket" in storage_s3.region_cache
        assert storage_s3.region_cache["west-bucket"] == "us-west-2"

        fh = storage_s3.get(west_url)
        assert fh.read().decode() == "west data"

        # Test accessing east bucket with nominal-style URL
        east_url = "s3://east-bucket/test.txt"
        storage_s3_east = osaka.storage.s3.S3()
        storage_s3_east.connect(east_url, params={"aws_access_key_id": "test", "aws_secret_access_key": "test"})

        # Verify region cache is populated
        assert "east-bucket" in storage_s3_east.region_cache
        assert storage_s3_east.region_cache["east-bucket"] == "us-east-1"

        fh_east = storage_s3_east.get(east_url)
        assert fh_east.read().decode() == "east data"

        storage_s3.close()
        storage_s3_east.close()

    @mock_aws
    def test_s3_virtual_hosted_style_url(self):
        """Test that osaka handles virtual-hosted style URLs correctly."""

        # Create bucket in us-west-2
        s3_west = boto3.client("s3", region_name="us-west-2")
        s3_west.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )
        s3_west.put_object(
            Bucket="test-bucket", Key="data.txt", Body="virtual hosted data"
        )

        # Test accessing with virtual-hosted style URL (region in hostname)
        storage_s3 = osaka.storage.s3.S3()
        virtual_hosted_url = "s3://s3.us-west-2.amazonaws.com/test-bucket/data.txt"
        storage_s3.connect(virtual_hosted_url)

        # This should use the region from the URL, not attempt detection
        assert storage_s3.is_nominal_style == False

        fh = storage_s3.get(virtual_hosted_url)
        assert fh.read().decode() == "virtual hosted data"

        storage_s3.close()

    @mock_aws
    def test_s3_legacy_style_url_with_port(self):
        """Test that osaka handles URLs with port correctly."""

        # Create bucket in us-west-2
        s3_west = boto3.client("s3", region_name="us-west-2")
        s3_west.create_bucket(
            Bucket="legacy-bucket",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )
        s3_west.put_object(
            Bucket="legacy-bucket", Key="legacy.txt", Body="legacy data"
        )

        # Test accessing with URL that includes port
        storage_s3 = osaka.storage.s3.S3()
        legacy_url = "s3://s3.us-west-2.amazonaws.com:80/legacy-bucket/legacy.txt"
        storage_s3.connect(legacy_url)

        # This should use the region from the URL
        assert storage_s3.is_nominal_style == False

        fh = storage_s3.get(legacy_url)
        assert fh.read().decode() == "legacy data"

        storage_s3.close()

    @mock_aws
    def test_s3_secure_url_variant(self):
        """Test that osaka handles s3s:// (secure) URLs correctly."""

        # Create bucket in us-west-2
        s3_west = boto3.client("s3", region_name="us-west-2")
        s3_west.create_bucket(
            Bucket="secure-bucket",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )
        s3_west.put_object(
            Bucket="secure-bucket", Key="secure.txt", Body="secure data"
        )

        # Test accessing with s3s:// nominal style URL
        storage_s3 = osaka.storage.s3.S3()
        secure_url = "s3s://secure-bucket/secure.txt"
        storage_s3.connect(secure_url, params={"aws_access_key_id": "test", "aws_secret_access_key": "test"})

        # Should be treated as nominal style and detect region
        assert storage_s3.is_nominal_style == True
        assert "secure-bucket" in storage_s3.region_cache
        assert storage_s3.region_cache["secure-bucket"] == "us-west-2"

        fh = storage_s3.get(secure_url)
        assert fh.read().decode() == "secure data"

        storage_s3.close()

    @mock_aws
    def test_s3_ensure_correct_region_fixes_wrong_endpoint(self):
        """Test that ensure_correct_region() corrects mismatched region in URL."""

        # Create bucket in us-west-2
        s3_west = boto3.client("s3", region_name="us-west-2")
        s3_west.create_bucket(
            Bucket="west-only-bucket",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )
        s3_west.put_object(
            Bucket="west-only-bucket", Key="data.txt", Body="west region data"
        )

        # Connect using eu-west-1 endpoint URL (WRONG region for this bucket)
        # The bucket() method should detect and switch to the correct region
        storage_s3 = osaka.storage.s3.S3()
        wrong_region_url = "s3://s3.eu-west-1.amazonaws.com/west-only-bucket/data.txt"
        storage_s3.connect(wrong_region_url)

        # Initially connected to eu-west-1 from URL
        assert storage_s3.is_nominal_style == False
        initial_region = storage_s3.s3.meta.client.meta.region_name
        assert initial_region == "eu-west-1"

        # When we access the bucket, ensure_correct_region() should fix it
        fh = storage_s3.get(wrong_region_url)
        assert fh.read().decode() == "west region data"

        # Verify the region cache was updated
        assert "west-only-bucket" in storage_s3.region_cache
        assert storage_s3.region_cache["west-only-bucket"] == "us-west-2"

        # Verify the S3 client switched to the correct region
        assert storage_s3.s3.meta.client.meta.region_name == "us-west-2"

        storage_s3.close()
