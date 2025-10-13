import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def handler(event, context):
    resp = table.scan()
    items = resp.get("Items", [])
    return {"statusCode": 200, "body": json.dumps(items)}
