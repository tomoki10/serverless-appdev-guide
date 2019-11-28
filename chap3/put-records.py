import boto3
import datetime
import time
import uuid

kinesis = boto3.client('kinesis')
stream_name = 'sample'

partition_key = str(uuid.uuid4())
data = datetime.datetime.utcnow().strftime('%s')

for i in range(15):
    kinesis.put_record(
        StreamName = stream_name,
        Data = data,
        PartitionKey = partition_key
    )