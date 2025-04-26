import json
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def lambda_handler(event, context):
    print('Event received:', json.dumps(event))
    
    # Add CORS headers to all responses
    headers = {
        "Access-Control-Allow-Origin": "*",  # Allow requests from any origin
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        "Content-Type": "application/json"
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'CORS preflight request successful'})
        }
    
    try:
        # Extract user from Authorization header or request body
        user_name = None
        
        # Check if we have headers (API Gateway event)
        if event.get('headers') and event.get('headers').get('Authorization'):
            # In a real scenario, you'd verify the token and extract user info
            # For simplicity, assuming user name is passed in request body
            body = {}
            if event.get('body'):
                if isinstance(event.get('body'), str):
                    body = json.loads(event.get('body'))
                else:
                    body = event.get('body')
            user_name = body.get('userName')
        else:
            # For direct Lambda invocations
            user_name = event.get('userName')
        
        if not user_name:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Missing userName parameter'})
            }
        
        # Get the Classes table name from environment variable or use default
        classes_table_name = os.environ.get('CLASSES_TABLE', 'Classes')
        classes_table = dynamodb.Table(classes_table_name)
        
        # Scan the table for classes where the user is a member
        response = classes_table.scan(
            FilterExpression=Attr('studentsList').contains(user_name) | Attr('facultyList').contains(user_name)
        )
        
        if not response.get('Items'):
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': 'No classes found for this user'})
            }
        
        # Collect all students from all classes user belongs to
        all_students = set()
        
        for class_item in response['Items']:
            if class_item.get('studentsList'):
                # Handle both string and list types for studentsList
                students_list = class_item['studentsList']
                
                # If studentsList is a string, split it
                if isinstance(students_list, str):
                    students_list = [s.strip() for s in students_list.split(',')]
                # If it's already a list, use it directly
                elif isinstance(students_list, list):
                    pass
                else:
                    print(f"Unexpected type for studentsList: {type(students_list)}")
                    continue
                
                # Add all students except the current user
                for student in students_list:
                    if student != user_name:  # Exclude the current user
                        all_students.add(student)
        
        # Convert set to list of objects for the response
        students = [{'name': student} for student in all_students]
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(students)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        # Add more detailed error logging
        import traceback
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'message': 'Server error', 'error': str(e)})
        }

