import json
import boto3
from boto3.dynamodb.conditions import Attr
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')

# Get environment variables
USERS_TABLE = os.environ['USERS_TABLE']
CLASSES_TABLE = os.environ['CLASSES_TABLE']
USER_POOL_ID = os.environ['USER_POOL_ID']

def lambda_handler(event, context):
    try:
        # Verify the request is authenticated and from an admin
        user = verify_admin(event)
        if not user:
            return build_response(403, {'message': 'Forbidden: Admin access required'})
        
        # Get query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        action = query_params.get('action')
        
        # Route based on the action
        if action == 'fetch':
            return fetch_users()
        elif action == 'delete':
            if event.get('body'):
                body = json.loads(event.get('body'))
                user_id = body.get('userId')
                return delete_user(user_id)
            return build_response(400, {'message': 'Missing request body or userId'})
        else:
            return build_response(400, {'message': 'Invalid action specified'})
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return build_response(500, {'message': 'Internal server error', 'error': str(e)})

def verify_admin(event):
    try:
        # Get the Authorization header
        headers = event.get('headers', {}) or {}
        auth_header = headers.get('Authorization') or headers.get('authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        # Extract the token
        token = auth_header.split(' ')[1]
        
        # Verify with Cognito
        # In a real implementation, you would validate the JWT token
        # For simplicity, we're using a DB lookup here
        users_table = dynamodb.Table(USERS_TABLE)
        response = users_table.scan(
            FilterExpression=Attr('role').eq('admin')
        )
        
        # This is a simplified check. In production, you'd validate the token properly
        admin_user = response.get('Items', [])[0] if response.get('Items') else None
        
        return admin_user
    
    except Exception as e:
        logger.error(f"Error verifying admin: {str(e)}")
        return None

def fetch_users():
    try:
        users_table = dynamodb.Table(USERS_TABLE)
        response = users_table.scan()
        
        return build_response(200, response.get('Items', []))
    
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise

def delete_user(user_id):
    try:
        if not user_id:
            return build_response(400, {'message': 'userId is required'})
        
        # 1. Get the user from DynamoDB to find their username
        users_table = dynamodb.Table(USERS_TABLE)
        user_response = users_table.get_item(
            Key={'userId': user_id}
        )
        
        user = user_response.get('Item')
        if not user:
            return build_response(404, {'message': 'User not found'})
        
        username = user.get('username')
        
        # 2. Delete user from Cognito
        try:
            cognito.admin_delete_user(
                UserPoolId=USER_POOL_ID,
                Username=username
            )
        except Exception as cognito_error:
            logger.error(f"Error deleting user from Cognito: {str(cognito_error)}")
            # Continue with DynamoDB deletion even if Cognito deletion fails
        
        # 3. Delete user from UserProfiles table
        users_table.delete_item(
            Key={'userId': user_id}
        )
        
        # 4. Remove user from all classes
        # First, get all classes
        classes_table = dynamodb.Table(CLASSES_TABLE)
        classes_response = classes_table.scan()
        
        classes = classes_response.get('Items', [])
        user_name = user.get('name', '')
        
        # Check each class for the user and update if needed
        for class_item in classes:
            update_needed = False
            update_expression = "SET "
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            # Check if user is in facultyList
            faculty_list = class_item.get('facultyList', [])
            if faculty_list and isinstance(faculty_list, list):
                # Find faculty matching the user name
                for i, faculty in enumerate(faculty_list):
                    faculty_name = faculty.get('S', '')
                    if faculty_name == user_name or user_name in faculty_name:
                        # Remove this faculty from the list
                        faculty_list.pop(i)
                        update_needed = True
                        update_expression += "#fl = :fl, "
                        expression_attribute_values[":fl"] = faculty_list
                        expression_attribute_names["#fl"] = "facultyList"
                        break
            
            # Check if user is in studentsList
            students_list = class_item.get('studentsList', [])
            if students_list and isinstance(students_list, list):
                # Find student matching the user name
                for i, student in enumerate(students_list):
                    student_name = student.get('S', '')
                    if student_name == user_name or user_name in student_name:
                        # Remove this student from the list
                        students_list.pop(i)
                        update_needed = True
                        update_expression += "#sl = :sl, "
                        expression_attribute_values[":sl"] = students_list
                        expression_attribute_names["#sl"] = "studentsList"
                        break
            
            # If the user is the main faculty, we'll clear that field
            faculty = class_item.get('faculty', '')
            if faculty and (faculty == user_name or user_name in faculty):
                update_needed = True
                update_expression += "#f = :f, "
                expression_attribute_values[":f"] = ""  # Empty the faculty field
                expression_attribute_names["#f"] = "faculty"
            
            # If updates are needed, perform them
            if update_needed:
                # Remove trailing comma and space
                update_expression = update_expression[:-2]
                
                classes_table.update_item(
                    Key={'classId': class_item['classId']},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values,
                    ExpressionAttributeNames=expression_attribute_names
                )
        
        return build_response(200, {
            'message': 'User deleted successfully',
            'userId': user_id
        })
    
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True
        },
        'body': json.dumps(body)
    }
