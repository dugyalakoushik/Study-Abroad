import json
import boto3
import uuid
import os  # <-- Add this line to import the 'os' module

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['CLASSES_TABLE'])  # Replace 'Classes' with your table name

def lambda_handler(event, context):
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST"
    }

    try:
        # Check if 'body' exists in event
        if 'body' not in event or not event['body']:
            return {
                "statusCode": 400,
                "headers": cors_headers,
                "body": json.dumps({"success": False, "message": "Request body is missing"})
            }

        body = json.loads(event['body'])

        # Extract data from the event
        class_name = body.get('className')
        faculty_name = body.get('facultyName')

        # Validate input data
        if not class_name or not faculty_name:
            return {
                "statusCode": 400,
                "headers": cors_headers,
                "body": json.dumps({"success": False, "message": "Class name and faculty name are required"})
            }

        # Generate a unique ID for the class
        class_id = str(uuid.uuid4())

        # Create the item to be inserted into DynamoDB
        class_item = {
            'classId': class_id,
            'name': class_name,
            'faculty': faculty_name,
            'members': 0,
            'lastActive': 'Just created'
        }

        # Insert the item into DynamoDB
        table.put_item(Item=class_item)

        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({"success": True, "message": "Class added successfully", "class": class_item})
        }

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"success": False, "message": f"Internal server error: {str(e)}"})
        }