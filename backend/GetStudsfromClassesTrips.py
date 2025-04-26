import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')

# Get table name from environment variables
CLS_TABLE_NAME = os.environ.get('CLS_TABLE')
table = dynamodb.Table(CLS_TABLE_NAME)

def lambda_handler(event, context):
    # CORS headers
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",  # Allow all origins
        "Access-Control-Allow-Methods": "POST, OPTIONS",  # Allow POST and OPTIONS
        "Access-Control-Allow-Headers": "Content-Type"  # Allow Content-Type header
    }

    try:
        # Handle preflight request (CORS)
        if event.get("httpMethod") == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"message": "CORS preflight request successful"})
            }

        # Parse request body
        body = json.loads(event.get("body", "{}"))
        class_id = body.get("classId")

        if not class_id:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"message": "Missing classId in request body"})
            }

        # Fetch class details from DynamoDB
        response = table.get_item(Key={"classId": class_id})
        class_data = response.get("Item")

        if not class_data:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"message": "Class not found"})
            }

        # Extract students list
        students_list = class_data.get("studentsList", [])

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"studentsList": students_list})
        }

    except Exception as e:
        print(f"Lambda Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"message": "Internal server error"})
        }
