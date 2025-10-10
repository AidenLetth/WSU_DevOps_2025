import json
import boto3
from datetime import datetime

# DynamoDB table name
DYNAMO_TABLE_NAME = 'AlarmLogs'


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMO_TABLE_NAME)

def lambda_handler(event, context):

    try:
        for record in event('Records', []):
            sns_message = record['Sns']['Message']
            #  DynamoDB
            table.put_item(
                Item={
                    'begin': f"{sns_message.get('AlarmName', 'N/A')}_{datetime.utcnow().isoformat()}",
                    'AlarmName': sns_message.get('AlarmName', 'N/A'),
                    'AlarmDescription': sns_message.get('AlarmDescription', 'N/A'),
                    'NewStateValue': sns_message.get('NewStateValue', 'N/A'),
                    'NewStateReason': sns_message.get('NewStateReason', 'N/A'),
                    'StateChangeTime': sns_message.get('StateChangeTime', 'N/A'),
                }
            )
            print(f"Logged alarm to DynamoDB: {sns_message}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('All alarms logged successfully!')
        }
    except Exception as e:
        print(f"Error logging alarm: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error logging alarms!')
        }
    
