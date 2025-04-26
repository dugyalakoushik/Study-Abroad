import json
import boto3
import uuid
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['CLASSES_TABLE'])

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")  # Log the incoming request
    
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps('CORS preflight successful')
        }
    elif event['httpMethod'] == 'POST':
        return create_class(event)
    elif event['httpMethod'] == 'GET':
        return get_all_classes()
    else:
        print("Unsupported HTTP method")  # Log unsupported HTTP method
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps('Unsupported HTTP method')
        }

def create_class(event):
    try:
        body = json.loads(event.get('body', '{}'))  # Safer handling of missing body
        class_name = body.get('className')
        faculty_name = body.get('facultyName')

        if not class_name or not faculty_name:
            print("Missing className or facultyName")  # Log missing fields
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({'error': 'Class name and faculty name are required'})
            }

        creation_time = datetime.now().isoformat()
        class_item = {
            'classId': str(uuid.uuid4()),
            'name': class_name,
            'faculty': faculty_name,
            'members': 0,
            'createdOn': creation_time
        }

        #save it to DB
        print(f"Saving class: {class_item}")  # Log the item being saved
        table.put_item(Item=class_item)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(class_item)
        }

    except Exception as e:
        print(f"Error in create_class: {e}")  # Log any errors
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'error': str(e)})
        }

def get_all_classes():
    try:
        response = table.scan()
        classes = response['Items']

        for class_item in classes:
            class_item['createdOn'] = class_item.get('createdOn', 'N/A')

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(classes, default=str)
        }

    except Exception as e:
        print(f"Error in get_all_classes: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'error': str(e)})
        }
