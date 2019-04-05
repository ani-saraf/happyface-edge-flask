import boto3
from utility import logger
REGION_NAME = 'us-east-1'
s3_bucket = 'image-recognition-edge'
s3_client = boto3.client('s3', region_name=REGION_NAME)
s3 = boto3.resource('s3', region_name=REGION_NAME)
bucket = s3.Bucket(s3_bucket)


def delete_objects():
    logger.info('Deleting Objects...')
    bucket.objects.filter(Prefix="thumbnail/").delete()
    logger.info('Objects Deleted')

