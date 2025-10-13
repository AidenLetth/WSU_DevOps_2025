import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def handler(event, context):
    body = json.loads(event.get("body", "{}"))
    url_id = body.get("url_id")
    new_url = body.get("url")
    if not url_id or not new_url:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing url_id or url"})}

    table.update_item(
        Key={"url_id": url_id},
        UpdateExpression="SET #u = :u",
        ExpressionAttributeNames={"#u": "url"},
        ExpressionAttributeValues={":u": new_url}
    )
    return {"statusCode": 200, "body": json.dumps({"message": "Updated", "url_id": url_id})}
