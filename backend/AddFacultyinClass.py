import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
CLS_TABLE_NAME = os.environ.get('CLS_TABLE')
table = dynamodb.Table(CLS_TABLE_NAME)

def lambda_handler(event, context):
    # Common CORS headers
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS, POST",
        "Access-Control-Allow-Headers": "Content-Type"
    }

    # Handle preflight (OPTIONS) request
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"message": "CORS preflight passed"})
        }

    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        faculty = body.get("faculty")
        class_id = body.get("classId")
        
        if not class_id or not faculty:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"message": "Missing classId or faculty"})
            }
        
        # Fetch existing class details
        response = table.get_item(Key={"classId": class_id})
        class_data = response.get("Item")

        if not class_data:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"message": "Class not found"})
            }

        # Update the facultyList (append if not already in list)
        faculty_list = class_data.get("facultyList", [])
        if faculty not in faculty_list:
            faculty_list.append(faculty)

            # Update DynamoDB
            table.update_item(
                Key={"classId": class_id},
                UpdateExpression="SET facultyList = :facultyList",
                ExpressionAttributeValues={":facultyList": faculty_list}
            )

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"message": "Faculty added successfully!"})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"message": "Internal server error"})
        }
