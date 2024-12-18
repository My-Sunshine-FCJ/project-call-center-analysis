import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Helper class để xử lý Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('analysis-results-it-got-talent')
        
        response = table.scan()
        items = response['Items']
        
        # Xử lý pagination nếu có
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
                'Content-Type': 'application/json'
            },
            # Sử dụng DecimalEncoder để serialize JSON
            'body': json.dumps(
                {
                    'success': True,
                    'data': items,
                    'count': len(items)
                },
                cls=DecimalEncoder
            )
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")  # Log error để debug
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }