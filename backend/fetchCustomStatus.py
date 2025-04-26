import json
import os
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.client('dynamodb')

def lambda_handler(event, context):
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 204, 'headers': cors_headers, 'body': ''}

    try:
        body = json.loads(event['body'])
        student_name = body['student_name']
        table_name = os.environ['DYNAMODB_TABLE']
        
        # Corrected query
        response = dynamodb.scan(
            TableName=table_name,
            FilterExpression='contains(studentsList, :student)',
            ExpressionAttributeValues={
                ':student': {'S': student_name}  # Now matches your data structure
            }
        )
        
        if not response['Items']:
            return {
                'statusCode': 404,
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Student not found in any class'})
            }
        
        # Process first matching class
        status_values = [item['S'] for item in response['Items'][0]['customstatus']['L']]
        
        return {
            'statusCode': 200,
            'headers': {**cors_headers, 'Content-Type': 'application/json'},
            'body': json.dumps({'customstatus': status_values})
        }
        
    except ClientError as e:
        print(f"DynamoDB Error: {e.response['Error']['Message']}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Database error. Check student name format.'})
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Internal server error'})
        }
