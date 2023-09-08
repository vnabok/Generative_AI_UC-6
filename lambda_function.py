import json
import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import logging

timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
BUCKET = os.environ['BUCKET']
FILE_NAME = f"metrics/volumes_metrics_{timestamp}.json"
OWNER_ID = os.environ['owner_id']

def get_volumes_metrics(response):
    unattached_disk_volumes = 0
    number_of_disk_volumes = 0
    overall_disk_size = 0
    unencrypted_disk_volumes = 0
    for volume in response['Volumes']:
        number_of_disk_volumes += 1
        overall_disk_size += volume['Size']
        if volume['Attachments'] == []:
            unattached_disk_volumes += 1
        if not volume['Encrypted']:
            unencrypted_disk_volumes += 1
    v_metric = {"Number_of_volumes": number_of_disk_volumes, "Overall_disk_size": overall_disk_size, "Unattached_disk_volumes": unattached_disk_volumes, "Unencrypted_disk_volumes": unencrypted_disk_volumes}
    return v_metric
def get_snapshots_metrics(response):
    overall_snapshots = 0
    unencrypted_snapshots = 0
    for snapshot in response['Snapshots']:
        overall_snapshots += 1
        if not snapshot['Encrypted']:
            unencrypted_snapshots += 1
    s_metric ={"Number of snapshots": overall_snapshots, "Unencrypted snapshots": unencrypted_snapshots}
    return s_metric

def upload_file(file_name, bucket, object):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object: S3 object Body
    :return: True if file was uploaded, else False
    """
    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.put_object(Key=file_name, Bucket=bucket, Body=object)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def main():
    ec2_client = boto3.client('ec2')
    volumes = ec2_client.describe_volumes()
    snapshots = ec2_client.describe_snapshots(OwnerIds=[f"{OWNER_ID}"])
    snapshots_metrics = get_snapshots_metrics(snapshots)
    volumes_metrics= get_volumes_metrics(volumes)
    final_metrics = {**volumes_metrics, **snapshots_metrics}
    metrics = json.dumps(final_metrics, sort_keys=True, indent=4)
    upload_file(FILE_NAME, BUCKET, metrics)
    return metrics

def lambda_handler(event, context):
    lambda_output = main()
    return {
        'statusCode': 200,
        'body': json.dumps('Lambda function output: {}'.format(lambda_output))
    }
