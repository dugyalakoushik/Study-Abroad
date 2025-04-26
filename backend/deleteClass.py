import json
import boto3
import os
from decimal import Decimal
import time

dynamodb = boto3.resource('dynamodb')

# Custom JSON encoder to handle Decimal and other non-serializable types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)  # Or float(obj) for decimal precision
        if isinstance(obj, int):  # Handle potential int values directly
            return int(obj)
        if isinstance(obj, float): # Handle potential float values directly
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    try:
        table_name = os.environ['CLASSES_TABLE']
        table = dynamodb.Table(table_name)
        
        # Extract class_id from the request body
        body = json.loads(event.get('body', '{}'))  # Safely parse the request body
        class_id = body.get('classId')
        
        if event['path'] == '/classes/getclassdetails':
        # Fetch the class details from DynamoDB
            response = table.get_item(Key={'classId': class_id})
            class_item = response.get('Item', {})
            
            # Extract the name and faculty from the dynamodb entry
            class_name = class_item.get('name', 'N/A')
            faculty_name = class_item.get('faculty', 'N/A')

            # construct a more appropriate body with only name and faculty
            response_body = {
              "name": class_name,
              "faculty": faculty_name
            }
        elif event['path'] == '/classes/deleteclass':
        # Delete the class from DynamoDB
            response = table.delete_item(Key={'classId': class_id})
            response_body = {"message": "Class deleted successfully"}
        # Fetch the class details from DynamoDB

        # No explicit conversion needed anymore, DecimalEncoder handles it
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS, POST",  # Added POST
                "Access-Control-Allow-Headers": "Content-Type, Authorization"  # Added Authorization
            },
            "body": json.dumps(response_body, cls=DecimalEncoder)  # Use the custom encoder
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS, POST",  # Added POST
                "Access-Control-Allow-Headers": "Content-Type, Authorization"  # Added Authorization
            },
            "body": json.dumps({"error": str(e)})
        }
