import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')

CLS_TABLE_NAME = os.environ.get('CLS_TABLE')
table = dynamodb.Table(CLS_TABLE_NAME)

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        student = body.get("student")
        class_id = body.get("classId")
        
        if not class_id or not student:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",  # Enable CORS
                    "Access-Control-Allow-Methods": "OPTIONS, POST",
                    "Access-Control-Allow-Headers": "Content-Type"
                },
                "body": json.dumps({"message": "Missing classId or student"})
            }
        
        # Fetch existing class details
        response = table.get_item(Key={"classId": class_id})
        class_data = response.get("Item")

        if not class_data:
            return {
                "statusCode": 404,
                "headers": {
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"message": "Class not found"})
            }

        # Update the studentsList (append if not already in list)
        students_list = class_data.get("studentsList", [])
        if student not in students_list:
            students_list.append(student)

        # Update DynamoDB
        table.update_item(
            Key={"classId": class_id},
            UpdateExpression="SET studentsList = :studentsList",
            ExpressionAttributeValues={":studentsList": students_list}
        )

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"message": "Student added successfully!"})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"message": "Internal server error"})
        }
