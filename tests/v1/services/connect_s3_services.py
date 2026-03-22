import os
from dotenv import load_dotenv
load_dotenv()
import boto3

# Create S3 client
s3_client = boto3.client(
    's3',
    endpoint_url='https://t3.storageapi.dev',
    aws_access_key_id=os.getenv('S3_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('S3_SECRET_ACCESS_KEY'),
    region_name='auto'
)

# Test connection - list buckets
try:
    response = s3_client.list_buckets()
    print("Buckets:", response['Buckets'])
except Exception as e:
    print(f"Connection failed: {e}")

# Upload a file
s3_client.put_object(
    Bucket=os.getenv('S3_BUCKET_NAME'),
    Key='test.txt',
    Body=b'Hello World'
)

# Download a file
response = s3_client.get_object(
    Bucket=os.getenv('S3_BUCKET_NAME'),
    Key='test.txt'
)
print(response['Body'].read())