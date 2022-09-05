import boto3

TABLE_NAME = "audio_table"

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url="http://localhost:8000",
    region_name="us-east1",
    aws_access_key_id="dummy_access_key",
    aws_secret_access_key="dummy_secret_key",
    verify=False,
)


response = dynamodb.create_table(
    TableName=TABLE_NAME,
    AttributeDefinitions=[{"AttributeName": "audio_id", "AttributeType": "S"}],
    KeySchema=[{"AttributeName": "audio_id", "KeyType": "HASH"}],
    ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
)
