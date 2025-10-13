import json
import os
import uuid
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def handler(event, context):
    body = json.loads(event.get("body", "{}"))
    url = body.get("url")
    if not url:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing url"})}

    url_id = str(uuid.uuid4())
    item = {"url_id": url_id, "url": url}
    table.put_item(Item=item)
    return {"statusCode": 201, "body": json.dumps(item)}
