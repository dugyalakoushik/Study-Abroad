import json
import boto3
import os
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['DYNAMODB_TABLE_NAME']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS, POST",
        "Access-Control-Allow-Headers": "Content-Type"
    }

    if event['httpMethod'] == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({})}

    try:
        # Parse request body
        body = json.loads(event['body'])
        faculty_name = body.get('facultyName', '').strip()
        status = body.get('status', '').strip()

        if not faculty_name or not status:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({"message": "Both facultyName and status are required"})
            }

        # Scan entire table and filter manually
        response = table.scan()
        matching_classes = []

        for item in response.get('Items', []):
            faculty_list = item.get('facultyList', [])
            
            # SAFE ITERATION WITH TYPE CHECKING
            if isinstance(faculty_list, list):
                for entry in faculty_list:
                    # Handle both map {"S": value} and direct string cases
                    if isinstance(entry, dict) and entry.get('S') == faculty_name:
                        matching_classes.append(item)
                        break
                    elif entry == faculty_name:  # Handle direct strings if they exist
                        matching_classes.append(item)
                        break

        print(f"Found {len(matching_classes)} matching classes for faculty: {faculty_name}")

        if not matching_classes:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({"message": f"No classes found for faculty: {faculty_name}"})
            }

        # Process first matching class
        class_record = matching_classes[0]
        class_id = class_record['classId']
        
        # Initialize customstatus if it doesn't exist
        if 'customstatus' not in class_record:
            print("Initializing customstatus field")
            table.update_item(
                Key={'classId': class_id},
                UpdateExpression="SET customstatus = :empty",
                ExpressionAttributeValues={':empty': []}
            )

        # Update custom status
        update_response = table.update_item(
            Key={'classId': class_id},
            UpdateExpression="SET #status = list_append(if_not_exists(#status, :empty), :newStatus)",
            ExpressionAttributeNames={'#status': 'customstatus'},
            ExpressionAttributeValues={
                ':empty': [],
                ':newStatus': [status]
            },
            ReturnValues="UPDATED_NEW"
        )

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                "message": "Status updated successfully",
                "classId": class_id,
                "updatedAttributes": update_response.get('Attributes', {})
            })
        }

    except ClientError as e:
        print(f"DynamoDB Error: {e.response['Error']['Message']}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({"message": "Database error", "details": str(e)})
        }
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({"message": "Processing error", "details": str(e)})
        }
