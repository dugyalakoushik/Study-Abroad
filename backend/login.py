'''import boto3
import os
import json
import hmac
import hashlib
import base64

cognito = boto3.client('cognito-idp')

USER_POOL_ID = os.environ.get('USER_POOL_ID')
CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET')

if not all([USER_POOL_ID, CLIENT_ID, CLIENT_SECRET]):
    raise ValueError("Missing required environment variables")

def calculate_secret_hash(username):
    message = username + CLIENT_ID
    secret = bytes(CLIENT_SECRET, 'utf-8')
    dig = hmac.new(secret, msg=message.encode('utf-8'), digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

def check_user_exists(email):
    try:
        cognito.admin_get_user(UserPoolId=USER_POOL_ID, Username=email)
        return True
    except cognito.exceptions.UserNotFoundException:
        return False

def get_user_attributes(email):
    try:
        user_info = cognito.admin_get_user(UserPoolId=USER_POOL_ID, Username=email)
        user_attributes = {attr['Name']: attr['Value'] for attr in user_info['UserAttributes']}
        return user_attributes
    except Exception as e:
        print(f"Error fetching user attributes for {email}: {str(e)}")
        return {}

def get_user_role(email):
    user_attributes = get_user_attributes(email)
    role = user_attributes.get('custom:userRole', None)
    print(f"Retrieved role for {email}: {role}")
    return role

def get_user_name(email):
    user_attributes = get_user_attributes(email)
    firstName = user_attributes.get('given_name', '')
    lastName = user_attributes.get('family_name', '')
    fullName = f"{firstName} {lastName}".strip()
    print(f"Retrieved name for {email}: {fullName}")
    return fullName

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        email = body['email']
        action = body.get('action', 'login')
        
        print(f"Processing {action} request for email: {email}")
        user_exists = check_user_exists(email)
        
        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        }
        
        if action == 'check':
            return {
                "statusCode": 200 if user_exists else 404,
                "headers": cors_headers,
                "body": json.dumps({
                    "success": user_exists,
                    "message": "User exists" if user_exists else "User not found"
                })
            }
            
        elif action == 'login':
            if not user_exists:
                return {"statusCode": 404, "headers": cors_headers, "body": json.dumps({"success": False, "message": "Login failed: User not found"})}
            if 'password' not in body:
                return {"statusCode": 400, "headers": cors_headers, "body": json.dumps({"success": False, "message": "Login failed: Password is required"})}
            
            secret_hash = calculate_secret_hash(email)
            auth_response = cognito.initiate_auth(
                AuthFlow='USER_PASSWORD_AUTH',
                ClientId=CLIENT_ID,
                AuthParameters={'USERNAME': email, 'PASSWORD': body['password'], 'SECRET_HASH': secret_hash}
            )
            tokens = auth_response.get('AuthenticationResult', {})
            role = get_user_role(email)
            name = get_user_name(email)
            
            print(f"Login successful for email: {email}, role: {role}, name: {name}")
            
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({
                    "success": True,
                    "message": f"Login successful for {email}",
                    "idToken": tokens.get('IdToken'),
                    "accessToken": tokens.get('AccessToken'),
                    "refreshToken": tokens.get('RefreshToken') if body.get('remember', False) else None,
                    "role": role,
                    "name": name,  # Include user's name
                    "expiresIn": tokens.get('ExpiresIn')  # Include expiry time
                })
            }
    except cognito.exceptions.NotAuthorizedException as e:
        return {"statusCode": 401, "headers": cors_headers, "body": json.dumps({"success": False, "message": f"Login failed: Incorrect password for {email}"})}
    except cognito.exceptions.UserNotConfirmedException:
        return {"statusCode": 403, "headers": cors_headers, "body": json.dumps({"success": False, "message": f"Login failed: User not confirmed: {email}"})}
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {"statusCode": 500, "headers": cors_headers, "body": json.dumps({"success": False, "message": "Internal server error"})}
'''

#allow only active trip users to login
import boto3
import os
import json
import hmac
import hashlib
import base64

cognito = boto3.client('cognito-idp')
dynamodb = boto3.client('dynamodb')

USER_POOL_ID = os.environ.get('USER_POOL_ID')
CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET')
CLASSES_TABLE = os.environ.get('CLASSES_TABLE', 'ClassesTrips')  # Add classes table name from environment variables

if not all([USER_POOL_ID, CLIENT_ID, CLIENT_SECRET]):
    raise ValueError("Missing required environment variables")

def calculate_secret_hash(username):
    message = username + CLIENT_ID
    secret = bytes(CLIENT_SECRET, 'utf-8')
    dig = hmac.new(secret, msg=message.encode('utf-8'), digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

def check_user_exists(email):
    try:
        cognito.admin_get_user(UserPoolId=USER_POOL_ID, Username=email)
        return True
    except cognito.exceptions.UserNotFoundException:
        return False

def get_user_attributes(email):
    try:
        user_info = cognito.admin_get_user(UserPoolId=USER_POOL_ID, Username=email)
        user_attributes = {attr['Name']: attr['Value'] for attr in user_info['UserAttributes']}
        return user_attributes
    except Exception as e:
        print(f"Error fetching user attributes for {email}: {str(e)}")
        return {}

def get_user_role(email):
    user_attributes = get_user_attributes(email)
    role = user_attributes.get('custom:userRole', None)
    print(f"Retrieved role for {email}: {role}")
    return role

def get_user_name(email):
    user_attributes = get_user_attributes(email)
    firstName = user_attributes.get('given_name', '')
    lastName = user_attributes.get('family_name', '')
    fullName = f"{firstName} {lastName}".strip()
    print(f"Retrieved name for {email}: {fullName}")
    return fullName

def check_user_in_classes(email, full_name=None):
    """
    Check if a user exists in any class by looking in both faculty and students lists.
    
    Args:
        email: Email or username of the user
        full_name: Full name of the user (optional, for additional checking)
        
    Returns:
        bool: True if the user exists in any class, False otherwise
    """
    try:
        # Scan the classes table
        response = dynamodb.scan(
            TableName=CLASSES_TABLE,
            Select='ALL_ATTRIBUTES'
        )
        
        if 'Items' not in response:
            print(f"No classes found in table {CLASSES_TABLE}")
            return False
            
        print(f"DEBUG - Looking for user {email} or {full_name} in class records")
        
        for class_item in response['Items']:
            class_id = class_item.get('classId', {}).get('S', 'unknown')
            print(f"DEBUG - Checking class {class_id}")
            
            # Check if user is in facultyList
            if 'facultyList' in class_item:
                faculty_list = []
                for item in class_item['facultyList']['L']:
                    if 'S' in item:
                        faculty_list.append(item['S'])
                
                print(f"DEBUG - Faculty list: {faculty_list}")
                
                if email in faculty_list or (full_name and full_name in faculty_list):
                    print(f"User {email} found in facultyList of class {class_id}")
                    return True
                    
            # Check if user is in studentsList
            if 'studentsList' in class_item:
                students_list = []
                for item in class_item['studentsList']['L']:
                    if 'S' in item:
                        students_list.append(item['S'])
                
                print(f"DEBUG - Students list: {students_list}")
                
                if email in students_list or (full_name and full_name in students_list):
                    print(f"User {email} found in studentsList of class {class_id}")
                    return True
        
        print(f"User {email} not found in any class")
        return False
        
    except Exception as e:
        print(f"Error checking user in classes: {str(e)}")
        # Default to True in case of errors to avoid blocking legitimate users
        # You may want to change this depending on your security requirements
        return True  # Changed to True to prevent login issues if there's a problem with class check

def lambda_handler(event, context):
    # Define CORS headers once
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "OPTIONS,POST"
    }
    
    # Handle OPTIONS request for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": ""
        }
    
    try:
        # Print the entire event for debugging
        print(f"DEBUG - Full event: {json.dumps(event)}")
        
        body = json.loads(event['body'])
        email = body['email']
        action = body.get('action', 'login')
        
        print(f"Processing {action} request for email: {email}")
        user_exists = check_user_exists(email)
        
        if action == 'check':
            return {
                "statusCode": 200 if user_exists else 404,
                "headers": cors_headers,
                "body": json.dumps({
                    "success": user_exists,
                    "message": "User exists" if user_exists else "User not found"
                })
            }
            
        elif action == 'login':
            if not user_exists:
                return {"statusCode": 404, "headers": cors_headers, "body": json.dumps({"success": False, "message": "Login failed: User not found"})}
            if 'password' not in body:
                return {"statusCode": 400, "headers": cors_headers, "body": json.dumps({"success": False, "message": "Login failed: Password is required"})}
            
            # Get user info first for class membership check
            name = get_user_name(email)
            
            # Get the user's role
            role = get_user_role(email)
            print(f"User role: {role}")
            
            # Skip class membership check for admins
            if role and role.lower() == "admin":
                user_in_class = True
                print(f"Skipping class check for admin user {email}")
            else:
                # Check if user is in any class
                print(f"Performing class check for {email} with name {name}")
                user_in_class = check_user_in_classes(email, name)
                print(f"Class check result for {email}: {user_in_class}")
                
                # Additional fallback: if we couldn't find the user in a class but we know they exist in Cognito,
                # try checking with their email as username
                if not user_in_class and '@' in email:
                    username = email.split('@')[0]
                    print(f"Trying fallback class check with username {username}")
                    user_in_class = check_user_in_classes(username, name)
                    print(f"Fallback class check result for {username}: {user_in_class}")
            
            if not user_in_class:
                return {"statusCode": 403, "headers": cors_headers, "body": json.dumps({
                    "success": False, 
                    "message": "Access denied: User not enrolled in any class",
                    "error": "NOT_IN_CLASS"
                })}
            
            # User exists in Cognito and is in a class (or is an admin), proceed with authentication
            try:
                secret_hash = calculate_secret_hash(email)
                auth_response = cognito.initiate_auth(
                    AuthFlow='USER_PASSWORD_AUTH',
                    ClientId=CLIENT_ID,
                    AuthParameters={'USERNAME': email, 'PASSWORD': body['password'], 'SECRET_HASH': secret_hash}
                )
                tokens = auth_response.get('AuthenticationResult', {})
                
                print(f"Login successful for email: {email}, role: {role}, name: {name}")
                
                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "success": True,
                        "message": f"Login successful for {email}",
                        "idToken": tokens.get('IdToken'),
                        "accessToken": tokens.get('AccessToken'),
                        "refreshToken": tokens.get('RefreshToken') if body.get('remember', False) else None,
                        "role": role,
                        "name": name,
                        "expiresIn": tokens.get('ExpiresIn')
                    })
                }
            except cognito.exceptions.NotAuthorizedException as e:
                print(f"Authentication error: {str(e)}")
                return {"statusCode": 401, "headers": cors_headers, "body": json.dumps({"success": False, "message": f"Login failed: Incorrect password for {email}"})}
            except cognito.exceptions.UserNotConfirmedException:
                return {"statusCode": 403, "headers": cors_headers, "body": json.dumps({"success": False, "message": f"Login failed: User not confirmed: {email}"})}
            except Exception as e:
                print(f"Cognito auth error: {str(e)}")
                return {"statusCode": 500, "headers": cors_headers, "body": json.dumps({"success": False, "message": f"Login error: {str(e)}"})}
                
    except cognito.exceptions.NotAuthorizedException as e:
        return {"statusCode": 401, "headers": cors_headers, "body": json.dumps({"success": False, "message": f"Login failed: Incorrect password for {email}"})}
    except cognito.exceptions.UserNotConfirmedException:
        return {"statusCode": 403, "headers": cors_headers, "body": json.dumps({"success": False, "message": f"Login failed: User not confirmed: {email}"})}
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {"statusCode": 500, "headers": cors_headers, "body": json.dumps({"success": False, "message": "Internal server error"})}
