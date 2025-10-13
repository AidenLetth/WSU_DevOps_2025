import json
import boto3
from datetime import datetime

# DynamoDB table name
DYNAMO_TABLE_NAME = 'AlarmLogs'




def lambda_handler(event, context):

    try:
            # Initialize DynamoDB resource 
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(DYNAMO_TABLE_NAME)
        print(f"Processing alarm event: {json.dumps(event)}")
        if 'Records' in event and event['Records']:
          # sns message 
            sns_message = json.loads(event['Records'][0]['Sns']['Message'])
            alarm_name = sns_message.get('AlarmName', 'unknown')
            new_state = sns_message.get('NewStateValue', 'unknown')
            reason = sns_message.get('NewStateReason', 'No reason provided')
        if new_state == 'ALARM':
                Item={
                    'begin': f"{sns_message.get('AlarmName', 'N/A')}_{datetime.utcnow().isoformat()}",
                    'AlarmName': sns_message.get('AlarmName', 'N/A'),
                    'AlarmDescription': sns_message.get('AlarmDescription', 'N/A'),
                    'NewStateValue': sns_message.get('NewStateValue', 'N/A'),
                    'NewStateReason': sns_message.get('NewStateReason', 'N/A'),
                    'StateChangeTime': sns_message.get('StateChangeTime', 'N/A'),
                }
        table.put_item(Item=Item)  
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
    
