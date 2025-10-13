import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def handler(event, context):
    body = json.loads(event.get("body", "{}"))
    url_id = body.get("url_id")
    if not url_id:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing url_id"})}

    table.delete_item(Key={"url_id": url_id})
    return {"statusCode": 200, "body": json.dumps({"message": "Deleted", "url_id": url_id})}
