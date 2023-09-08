import logging
import boto3
from botocore.exceptions import ClientError
import json

# Create a bucket policy
account_id = "111122223333"
bucket_name = "vn-generative-ai-uc-6"
role_name = "vn_generative_ai_uc_6_role"
bucket_policy = {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AddS3Permission",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Effect": "Allow",
      "Resource": f"arn:aws:s3:::{bucket_name}/*",
      "Principal": {
        "AWS": [
          f"arn:aws:iam::{account_id}:role/{role_name}"
        ]
      }
    }
  ]
}

bucket_lifecycle_policy = {
    'Rules': [
        {
            'Expiration': {
                'Days': 365,
            },
            'Filter': {
                'Prefix': 'metrics/',
            },
            'ID': 'TestOnly',
            'Status': 'Enabled',
            'Transitions': [
                {
                    'Days': 30,
                    'StorageClass': 'GLACIER',
                },
            ],
        },
    ],
}



# Convert the policy from JSON dict to string
bucket_policy = json.dumps(bucket_policy)

def create_bucket(bucket_name, bucket_policy, bucket_lifecycle_policy, region=None):
    """Create an S3 bucket in a specified region

    If a region is not specified, the bucket is created in the S3 default
    region (us-east-1).

    :param bucket_name: Bucket to create
    :param region: String region to create bucket in, e.g., 'us-west-2'
    :return: True if bucket created, else False
    """

    # Create bucket
    try:
        if region is None:
            s3_client = boto3.client('s3')
            s3_client.create_bucket(Bucket=bucket_name)
            # Set the new policy
            s3_client.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)
            s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=bucket_lifecycle_policy
            )
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name,
                                    CreateBucketConfiguration=location)
            s3_client.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)
            s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=bucket_lifecycle_policy
            )
    except ClientError as e:
        logging.error(e)
        return False
    return True

if __name__ == "__main__":
    create_bucket(bucket_name, bucket_policy, bucket_lifecycle_policy, region="eu-central-1")
